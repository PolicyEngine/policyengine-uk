"""Synthetic regressions for FA 2004 ss. 188, 190, 228ZA and 233.

The NICs-only salary-sacrifice cap must preserve annual-allowance inputs,
including after age 75 and at the basic RAS relief boundary. Charge
comparisons either keep ordinary tax bands stable or hold ordinary tax
inputs fixed; unrestricted charge invariance is not asserted.
"""

import numpy as np

import pytest

from hypothesis import HealthCheck, given, settings

from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")


def make_sim(year, **values):
    s = Simulation(
        situation={
            "people": {"p": {k: {year: v} for k, v in values.items()}},
            "benunits": {"b": {"members": ["p"]}},
            "households": {"h": {"members": ["p"]}},
        }
    )
    s.apply_parameter_changes(
        {
            "gov.contrib.behavioral_responses.salary_sacrifice_broad_base_haircut_rate": {
                str(year): 0
            }
        }
    )
    return s


@pytest.mark.parametrize("year", [2029, 2030])
@pytest.mark.parametrize("scheme", ["DC", "DB"])
def test_nics_cap_does_not_create_taper_after_age75(year, scheme):
    values = dict(
        age=80,
        employment_income_before_lsr=160000,
        pension_contributions_via_salary_sacrifice=30000,
        employer_pension_contributions=100000,
    )
    if scheme == "DB":
        values["pension_contributions_for_annual_allowance"] = 150000
    s = make_sim(year, **values)
    actual = {
        v: float(s.calculate(v, year)[0])
        for v in [
            "pension_contributions_for_annual_allowance",
            "pension_annual_allowance_threshold_income",
            "pension_annual_allowance_adjusted_income",
            "pension_annual_allowance",
            "personal_pension_contributions_tax",
        ]
    }
    # The full 30,000 sacrifice raises 160,000 cash pay to threshold 190,000.
    # The 28,000 returned for NICs remains employer pension provision in law.
    assert actual["pension_annual_allowance_threshold_income"] == 190000
    assert actual["pension_annual_allowance"] == 60000
    assert actual["personal_pension_contributions_tax"] == (
        31500 if scheme == "DC" else 40500
    )


def _population_simulation(people, year, cap=2_000):
    situation = {"people": {}, "benunits": {}, "households": {}}
    for index, values in enumerate(people):
        name = f"p{index}"
        situation["people"][name] = {
            key: {year: value} for key, value in values.items()
        }
        situation["benunits"][f"b{index}"] = {"members": [name]}
        situation["households"][f"h{index}"] = {"members": [name]}
    sim = Simulation(situation=situation)
    sim.apply_parameter_changes(
        {
            "gov.hmrc.national_insurance.salary_sacrifice_pension_cap": {
                str(year): cap
            },
            "gov.contrib.behavioral_responses.salary_sacrifice_broad_base_haircut_rate": {
                str(year): 0
            },
        }
    )
    return sim


@pytest.mark.parametrize("year", [2029, 2030])
def test_nics_cap_preserves_basic_ras_threshold_income_boundary(year):
    """Sections 190(2)-(4) and 191(7) preserve the full basic RAS amount."""
    values = {
        "age": 45,
        "employment_income_before_lsr": 2_000,
        "pension_contributions_via_salary_sacrifice": 201_000,
        "employer_pension_contributions": 100_000,
        "personal_pension_contributions": 3_600,
    }
    for cap in [2_000, float("inf")]:
        sim = _population_simulation([values], year, cap)
        # Cash pay plus full sacrifice less the full basic RAS relief.
        expected = {
            "pension_contributions_for_annual_allowance": 304_600,
            "pension_annual_allowance_threshold_income": 199_400,
            "pension_annual_allowance_adjusted_income": 303_000,
            "pension_annual_allowance": 60_000,
        }
        for variable, amount in expected.items():
            assert float(sim.calculate(variable, year)[0]) == amount, (cap, variable)

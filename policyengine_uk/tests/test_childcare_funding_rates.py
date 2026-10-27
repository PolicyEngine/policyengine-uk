"""DfE combined national-average funding is the model's hourly valuation.

Table 6 of each funding-year technical note supplies the rate oracles. These
are local-authority funding averages, not individual providers' fees. The
existing annual model samples 30 April, without blending the hours rollout.
"""

from pathlib import Path

import numpy as np
import pytest
from policyengine_core.parameters import load_parameter_file

from policyengine_uk import Simulation
from policyengine_uk.tax_benefit_system import system

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
RATES = {
    2024: [11.22, 8.28, 5.88],
    2025: [11.54, 8.53, 6.12],
    2026: [12.04, 8.90, 6.61],
}
AGES = np.array([1, 2, 3])


def working_family(year, country="ENGLAND", child_hours=30, family_hours=30):
    people = {"parent": {"age": {year: 35}, "employment_income": {year: 30_000}}}
    people.update(
        {
            f"child{age}": {
                "age": {year: age},
                "max_free_entitlement_hours_used": {year: child_hours},
            }
            for age in (1, 2, 3)
        }
    )
    members = list(people)
    return {
        "people": people,
        "benunits": {
            "family": {
                "members": members,
                "maximum_extended_childcare_hours_usage": {year: family_hours},
            }
        },
        "households": {"home": {"members": members, "country": {year: country}}},
    }


@pytest.mark.parametrize("year", [2025, 2026])
def test_published_april_rates_and_prior_day(year):
    raw = load_parameter_file(
        str(
            Path(__file__).parents[1] / "parameters/gov/dfe/childcare_funding_rate.yaml"
        ),
        "childcare_funding_rate",
    )
    np.testing.assert_allclose(
        raw(f"{year}-04-01").calc(AGES), RATES[year], rtol=0, atol=1e-10
    )
    np.testing.assert_allclose(
        raw(f"{year}-03-31").calc(AGES), RATES[year - 1], rtol=0, atol=1e-10
    )


@pytest.mark.parametrize("year", [2024, 2025, 2026])
def test_april_anchors_reach_processed_annual_rates(year):
    rates = system.parameters(str(year)).gov.dfe.childcare_funding_rate
    np.testing.assert_allclose(rates.calc(AGES), RATES[year], rtol=0, atol=1e-10)


@pytest.mark.parametrize(
    "year,universal,extended_per_child,extended_total",
    [
        (2025, [0, 0, 0, 2325.60], [0, 6577.80, 5434.00, 5567.00], 17578.80),
        (2026, [0, 0, 0, 2511.80], [0, 13725.60, 11339.20, 5893.80], 30958.60),
    ],
)
def test_published_rates_reach_genuine_working_family_awards(
    year, universal, extended_per_child, extended_total
):
    sim = Simulation(situation=working_family(year))
    # 2025 retains the existing 15-hour under-three annual schedule; 2026
    # gives 30. Whole ages imply 6 April birthdays: the age-three child
    # starts universal provision in September, and age-two funding begins
    # after the second-birthday term. Each common term uses one age-band rate.
    np.testing.assert_allclose(
        sim.calculate("universal_childcare_entitlement", year),
        universal,
        rtol=0,
        atol=0.02,
    )
    np.testing.assert_allclose(
        sim.calculate("extended_childcare_entitlement_per_child", year),
        extended_per_child,
        rtol=0,
        atol=0.02,
    )
    np.testing.assert_allclose(
        sim.calculate("extended_childcare_entitlement", year),
        extended_total,
        rtol=0,
        atol=0.02,
    )


@pytest.mark.parametrize("year,expected", [(2025, 3241.40), (2026, 3382.00)])
def test_published_rates_reach_targeted_award_for_reported_qualifying_benefit(
    year, expected
):
    # An ordinary reported Income Support award is an existing qualifying
    # benefit input. Eligibility and the childcare amount are calculated.
    # Born 6 April, the child receives two targeted terms from September.
    sim = Simulation(
        situation={
            "people": {"parent": {"age": {year: 35}}, "child": {"age": {year: 2}}},
            "benunits": {
                "family": {
                    "members": ["parent", "child"],
                    "income_support": {year: 1000},
                }
            },
            "households": {
                "home": {"members": ["parent", "child"], "country": {year: "ENGLAND"}}
            },
        }
    )
    np.testing.assert_allclose(
        sim.calculate("targeted_childcare_entitlement", year),
        [0, expected],
        rtol=0,
        atol=0.01,
    )


@pytest.mark.parametrize("child_hours,family_hours", [(10, 30), (30, 10)])
def test_child_and_family_usage_limits_keep_the_published_rate(
    child_hours, family_hours
):
    sim = Simulation(
        situation=working_family(
            2026, child_hours=child_hours, family_hours=family_hours
        )
    )
    # A one-year-old gets min(30,10) * 38 * £12.04, with no base hours.
    assert sim.calculate("extended_childcare_entitlement_per_child", 2026)[
        1
    ] == pytest.approx(4575.20, abs=0.01)


def test_outside_england_retains_zero_entitlements():
    sim = Simulation(situation=working_family(2026, country="WALES"))
    for variable in (
        "universal_childcare_entitlement",
        "targeted_childcare_entitlement",
        "extended_childcare_entitlement",
    ):
        assert not np.asarray(sim.calculate(variable, 2026)).any()


def test_existing_cpi_projection_starts_from_the_2026_funding_anchor():
    # This verifies the retained projection rule, not an official 2027 rate.
    p = system.parameters
    index = p.gov.economic_assumptions.indices.obr.lagged_cpi
    factor = index("2027") / index("2026")
    expected = np.array([12.04, 8.90, 6.61]) * factor
    np.testing.assert_allclose(
        p("2027").gov.dfe.childcare_funding_rate.calc(AGES), expected, rtol=0, atol=1e-8
    )

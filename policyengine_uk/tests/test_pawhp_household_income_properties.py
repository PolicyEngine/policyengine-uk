"""The Pension Age Winter Heating Payment counts once in household income.

pawhp was in gov_spending but not in household_benefits,
hbai_household_net_income or hbai_benefits, so Scottish pensioners' winter
heating payment was missing from household net income and HBAI income.

Differential property, for any population of households in any country and
the 2023 to 2027 qualifying weeks: switching PAWHP off
(gov.social_security_scotland.pawhp.active) lowers household_benefits,
household_gross_income, household_net_income, hbai_benefits and
hbai_household_net_income by exactly the household's pawhp, and changes
neither the Winter Fuel Payment nor the Cost-of-Living Payments (the
pensioner payment is keyed on the Winter Fuel Payment). Before the fix the
income measures did not move at all.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEARS = [2023, 2024, 2025, 2026, 2027]
COUNTRIES = ["ENGLAND", "WALES", "SCOTLAND", "NORTHERN_IRELAND"]
# Either side of pensionable age (66 to 67 over these years) and of 80.
AGES = [40, 60, 67, 70, 79, 80, 85]
INCOME_MEASURES = [
    "household_benefits",
    "household_gross_income",
    "household_net_income",
    "hbai_benefits",
    "hbai_household_net_income",
]
UNCHANGED = ["winter_fuel_allowance", "cost_of_living_support_payment"]
PAWHP_OFF = {"gov.social_security_scotland.pawhp.active": False}
PROPERTY_SETTINGS = settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@st.composite
def benefit_units(draw):
    return {
        "adults": [
            {
                "age": draw(st.sampled_from(AGES)),
                "state_pension_reported": draw(st.sampled_from([0, 8_000, 12_000])),
                "employment_income": draw(st.sampled_from([0, 0, 15_000, 60_000])),
            }
            for _ in range(draw(st.integers(1, 2)))
        ],
        # None leaves Pension Credit to the model's own means test.
        "pension_credit": draw(st.sampled_from([None, 0, 1_000])),
    }


@st.composite
def populations(draw):
    return {
        "year": draw(st.sampled_from(YEARS)),
        "households": [
            {
                "country": draw(st.sampled_from(COUNTRIES)),
                "units": draw(st.lists(benefit_units(), min_size=1, max_size=2)),
            }
            for _ in range(draw(st.integers(1, 4)))
        ],
    }


def situation(population):
    year = population["year"]
    people, benunits, households = {}, {}, {}
    for h, household in enumerate(population["households"]):
        members = []
        for u, unit in enumerate(household["units"]):
            unit_members = []
            for a, adult in enumerate(unit["adults"]):
                name = f"h{h}_u{u}_a{a}"
                people[name] = {key: {year: value} for key, value in adult.items()}
                unit_members.append(name)
            benunits[f"h{h}_u{u}"] = {"members": unit_members}
            if unit["pension_credit"] is not None:
                benunits[f"h{h}_u{u}"]["pension_credit"] = {
                    year: unit["pension_credit"]
                }
            members += unit_members
        households[f"h{h}"] = {
            "members": members,
            "country": {year: household["country"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


@PROPERTY_SETTINGS
@given(populations())
def test_switching_pawhp_off_lowers_household_income_by_pawhp(population):
    year = population["year"]
    reformed = Simulation(situation=situation(population), reform=PAWHP_OFF)
    baseline = reformed.baseline
    pawhp = baseline.calculate("pawhp", year)
    assert np.all(reformed.calculate("pawhp", year) == 0)
    for measure in INCOME_MEASURES:
        change = baseline.calculate(measure, year) - reformed.calculate(measure, year)
        np.testing.assert_allclose(change, pawhp, atol=1e-2, err_msg=measure)
    for name in UNCHANGED:
        np.testing.assert_allclose(
            baseline.calculate(name, year),
            reformed.calculate(name, year),
            atol=1e-6,
            err_msg=name,
        )


def test_pawhp_is_paid_in_the_generated_populations():
    """The property is not vacuous: a Scottish pensioner household gets PAWHP
    from 2024, and switching it off changes household net income."""
    population = {
        "year": 2025,
        "households": [
            {
                "country": "SCOTLAND",
                "units": [
                    {
                        "adults": [
                            {
                                "age": 70,
                                "state_pension_reported": 12_000,
                                "employment_income": 0,
                            }
                        ],
                        "pension_credit": 0,
                    }
                ],
            }
        ],
    }
    reformed = Simulation(situation=situation(population), reform=PAWHP_OFF)
    baseline = reformed.baseline
    assert baseline.calculate("pawhp", 2025)[0] > 200
    change = baseline.calculate("household_net_income", 2025) - reformed.calculate(
        "household_net_income", 2025
    )
    assert change[0] == pytest.approx(baseline.calculate("pawhp", 2025)[0], abs=1e-2)

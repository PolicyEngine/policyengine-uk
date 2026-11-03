"""The Pension Age Winter Heating Payment counts once in household income.

pawhp was in gov_spending but not in household_benefits,
hbai_household_net_income or hbai_benefits, so Scottish pensioners' winter
heating payment was missing from household net income and HBAI income.

Differential property, for any population of households in any country and
the 2023 to 2027 qualifying weeks: switching PAWHP off
(gov.social_security_scotland.pawhp.active) lowers household_benefits,
household_gross_income and hbai_benefits by exactly the household's pawhp,
and household_net_income and HBAI income (before the reset of a negative
figure to zero) by its pawhp less the change in the household's income tax. It changes neither the Winter
Fuel Payment nor the Cost-of-Living Payments (the pensioner payment is
keyed on the Winter Fuel Payment). Before the fix the income measures did
not move at all.

The income tax term is zero here. It keeps the property true once a charge
on the payment (ITEPA 2003 s.681I, recovering it from people with total
income over £35,000) is modelled in income tax: the net measures then fall
by the payment net of the charge, and income tax falls by the charge,
which is at least zero and at most the payment.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEARS = [2023, 2024, 2025, 2026, 2027]
COUNTRIES = ["ENGLAND", "WALES", "SCOTLAND", "NORTHERN_IRELAND"]
# Either side of pensionable age (66 to 67 over these years) and of 80.
AGES = [40, 60, 67, 70, 79, 80, 85]
GROSS_MEASURES = ["household_benefits", "household_gross_income", "hbai_benefits"]
# HBAI income before the reset to zero: the accounting identity holds for the
# sum of components, which the reset would break for a negative income.
NET_MEASURES = [
    "household_net_income",
    "hbai_household_net_income_before_reset_to_zero",
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


# PAWHP recipients the property always checks, whatever Hypothesis draws: a
# single Scottish pensioner in 2025, when everyone of pensionable age in
# Scotland is entitled, and a Scottish couple on Pension Credit in 2024, when
# a relevant benefit was a condition and one member's payment is the couple's.
PAWHP_RECIPIENTS = [
    {
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
    },
    {
        "year": 2024,
        "households": [
            {
                "country": "SCOTLAND",
                "units": [
                    {
                        "adults": [
                            {
                                "age": 70,
                                "state_pension_reported": 8_000,
                                "employment_income": 0,
                            },
                            {
                                "age": 82,
                                "state_pension_reported": 8_000,
                                "employment_income": 0,
                            },
                        ],
                        "pension_credit": 1_000,
                    }
                ],
            }
        ],
    },
]


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
                # Each unit's adults are its claimant and partner, however far
                # apart their ages (40 and 85 are drawn).
                people[name]["is_claimant_or_partner"] = {year: True}
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
@example(PAWHP_RECIPIENTS[0])
@example(PAWHP_RECIPIENTS[1])
def test_switching_pawhp_off_lowers_household_income_by_pawhp(population):
    year = population["year"]
    reformed = Simulation(situation=situation(population), reform=PAWHP_OFF)
    baseline = reformed.baseline
    pawhp = baseline.calculate("pawhp", year)
    assert np.all(reformed.calculate("pawhp", year) == 0)

    def change(name):
        """The fall in a household total, and the tolerance for comparing it:
        1p plus two float32 steps at the total's size (values are stored as
        float32, whose step is 1.6p at £150,000)."""
        before = baseline.calculate(name, year, map_to="household")
        after = reformed.calculate(name, year, map_to="household")
        tolerance = 1e-2 + 2 * np.spacing(np.abs(before).astype(np.float32))
        return before - after, tolerance

    tax_change, tax_tolerance = change("income_tax")
    assert np.all(tax_change >= -tax_tolerance)
    assert np.all(tax_change <= pawhp + tax_tolerance)
    for measure in GROSS_MEASURES:
        fall, tolerance = change(measure)
        assert np.all(np.abs(fall - pawhp) <= tolerance), measure
    for measure in NET_MEASURES:
        fall, tolerance = change(measure)
        assert np.all(np.abs(fall - (pawhp - tax_change)) <= tolerance), measure
    for name in UNCHANGED:
        np.testing.assert_allclose(
            baseline.calculate(name, year),
            reformed.calculate(name, year),
            atol=1e-6,
            err_msg=name,
        )


@pytest.mark.parametrize("population", PAWHP_RECIPIENTS)
def test_the_property_examples_receive_pawhp(population):
    """The property is not vacuous: each of its explicit examples is a
    household that receives PAWHP, and switching PAWHP off lowers its
    household net income by the payment."""
    year = population["year"]
    reformed = Simulation(situation=situation(population), reform=PAWHP_OFF)
    baseline = reformed.baseline
    pawhp = baseline.calculate("pawhp", year)
    assert pawhp[0] > 0
    change = baseline.calculate("household_net_income", year) - reformed.calculate(
        "household_net_income", year
    )
    assert change[0] == pytest.approx(pawhp[0], abs=1e-2)

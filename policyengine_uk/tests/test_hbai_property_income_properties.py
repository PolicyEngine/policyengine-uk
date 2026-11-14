"""Property tests for landlords' finance costs in household income (#2390).

HBAI income and market income count a landlord's profit after the costs of
dwelling-related loans, as the Family Resources Survey records it: rent from
property after the mortgage payments and loan interest on show card K6.
Income tax does not deduct those costs (ITTOIA 2005 s. 272A(4)) and relieves
them by a reduction at the property basic rate instead (s. 274A). So finance
costs lower market income by the costs taken off the profit, and lower HBAI
income by those costs less the tax they save: they never raise it.

Each generated landlord is simulated twice, without and with finance costs,
and the two are compared.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2027
OTHER_EMPLOYMENT_INCOME = [0, 8_000, 13_000, 30_000, 60_000, 110_000, 200_000]
# Every third person is a Scottish taxpayer.
SCOTTISH = [i % 3 == 2 for i in range(7)]
CASES = 21  # Each case is simulated without and with its finance costs.
PEOPLE = 2 * CASES
# Benefits that can count property income after finance costs, and so can
# rise with them; HBAI counts each of them.
MEANS_TESTED_BENEFITS = [
    "universal_credit",
    "housing_benefit",
    "council_tax_benefit",
    "income_support",
    "pension_credit",
    "working_tax_credit",
    "child_tax_credit",
    "esa_income",
    "jsa_income",
]

amount = st.one_of(
    st.floats(min_value=0, max_value=2_500),
    st.floats(min_value=0, max_value=60_000),
    st.sampled_from([0.0, 1_000.0, 12_570.0]),
)
case = st.tuples(
    st.one_of(amount, st.floats(min_value=-3_000, max_value=0)),  # profit
    amount,  # finance costs
    amount,  # expenses
    st.booleans(),  # receipts known (profit + expenses) or unknown
)
cases = st.lists(case, min_size=CASES, max_size=CASES)


def person_index(i):
    return i % CASES % len(OTHER_EMPLOYMENT_INCOME)


@pytest.fixture(scope="module")
def sim():
    people = {
        f"person_{i}": {
            "age": {YEAR: 40},
            "employment_income": {YEAR: OTHER_EMPLOYMENT_INCOME[person_index(i)]},
            "property_income": {YEAR: 0},
            "property_rental_income": {YEAR: 0},
            "property_finance_costs": {YEAR: 0},
        }
        for i in range(PEOPLE)
    }
    households = {
        f"household_{i}": {
            "members": [f"person_{i}"],
            "region": {YEAR: "SCOTLAND" if SCOTTISH[person_index(i)] else "LONDON"},
        }
        for i in range(PEOPLE)
    }
    return Simulation(
        situation={
            "people": people,
            "benunits": {
                f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(PEOPLE)
            },
            "households": households,
        }
    )


def run(sim, drawn):
    profit, costs, expenses, known = map(np.array, zip(*drawn))
    receipts = np.where(known, np.maximum(profit, 0) + expenses, 0)
    sim.set_input("property_income", YEAR, np.concatenate([profit, profit]))
    sim.set_input("property_rental_income", YEAR, np.concatenate([receipts] * 2))
    sim.set_input(
        "property_finance_costs", YEAR, np.concatenate([np.zeros(CASES), costs])
    )
    sim.reset_calculations()

    def change(variable):
        values = sim.calculate(variable, YEAR).astype(float)
        return values[:CASES], values[CASES:] - values[:CASES]

    stored_profit, _ = change("property_income")
    _, stored_costs = change("property_finance_costs")
    income_tax, income_tax_change = change("income_tax")
    benefits_change = sum(change(variable)[1] for variable in MEANS_TESTED_BENEFITS)
    return dict(
        # The costs taken off the profit: all of them up to a positive profit,
        # and none from a loss.
        deducted=np.minimum(stored_costs, np.maximum(stored_profit, 0)),
        market_income=change("market_income")[1],
        household_market_income=change("household_market_income")[1],
        hbai=change("hbai_household_net_income_before_reset_to_zero")[1],
        national_insurance=change("national_insurance")[1],
        income_tax=income_tax,
        income_tax_change=income_tax_change,
        benefits=benefits_change,
        rate=sim.tax_benefit_system.parameters(
            f"{YEAR}-01-01"
        ).gov.hmrc.income_tax.rates.property.basic,
    )


def tolerance(*values):
    """A penny plus float32 rounding on the amounts involved."""
    return 0.01 + 1e-6 * sum(np.abs(v) for v in values)


SETTINGS = settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(cases)
def test_finance_costs_lower_market_and_hbai_income(sim, drawn):
    r = run(sim, drawn)
    tax_saved = -r["income_tax_change"]
    margin = tolerance(r["deducted"], r["income_tax"], r["hbai"])
    # Market income falls by the costs taken off the profit.
    assert (np.abs(r["market_income"] + r["deducted"]) <= margin).all()
    assert (np.abs(r["household_market_income"] + r["deducted"]) <= margin).all()
    # The reduction saves at most the property basic rate on those costs, and
    # finance costs never raise tax or change NI.
    assert (tax_saved >= -margin).all()
    assert (tax_saved <= r["rate"] * r["deducted"] + margin).all()
    assert (np.abs(r["national_insurance"]) <= margin).all()
    # HBAI income moves by the costs, the tax saved and any means-tested
    # benefit that counts property income after the costs, and nothing else.
    expected = -r["deducted"] + tax_saved + r["benefits"]
    assert (np.abs(r["hbai"] - expected) <= margin).all()
    # So, before any benefit response, finance costs never raise HBAI income.
    assert (r["hbai"] - r["benefits"] <= margin).all()

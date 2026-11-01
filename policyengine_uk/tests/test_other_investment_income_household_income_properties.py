"""Property tests for other investment income in household income.

Income tax charges other investment income (interest on National Savings and
Investments products, gilts and other securities, and from trusts) as savings
income through taxable_savings_interest_income, exactly as it charges bank
interest. HBAI counts investment income, which the Family Resources Survey
defines as the interest and dividends received on savings and investments,
NS&I products and gilts included. So every household income measure must
count a pound of other investment income as it counts a pound of bank
interest. Household net income used to take off the tax on it without adding
the income, so the interest lowered net income.

Each generated case is simulated three times: with no interest, with the
amount as bank interest and with it as other investment income.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2027
EMPLOYMENT_INCOME = [0, 8_000, 13_000, 30_000, 60_000, 110_000, 200_000]
# Every third pay level (£13,000 and £110,000) is in Scotland.
SCOTTISH = [i % 3 == 2 for i in range(len(EMPLOYMENT_INCOME))]
CASES = 21
# Each case is simulated with no interest, bank interest and other investment
# income, in that order.
PEOPLE = 3 * CASES
VARIABLES = [
    "income_tax",
    "market_income",
    "capital_income",
    "household_market_income",
    "household_gross_income",
    "household_net_income",
    "hbai_household_net_income_before_reset_to_zero",
]

amount = st.one_of(
    st.floats(min_value=0, max_value=2_500),
    st.floats(min_value=0, max_value=60_000),
    st.sampled_from([0.0, 500.0, 1_000.0, 5_000.0]),
)
amounts = st.lists(amount, min_size=CASES, max_size=CASES)


def person_index(i):
    return i % CASES % len(EMPLOYMENT_INCOME)


@pytest.fixture(scope="module")
def sim():
    people = {
        f"person_{i}": {
            "age": {YEAR: 40},
            "employment_income": {YEAR: EMPLOYMENT_INCOME[person_index(i)]},
            "savings_interest_income": {YEAR: 0},
            "other_investment_income": {YEAR: 0},
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
    interest = np.asarray(drawn, dtype=float)
    none = np.zeros(CASES)
    sim.set_input(
        "savings_interest_income", YEAR, np.concatenate([none, interest, none])
    )
    sim.set_input(
        "other_investment_income", YEAR, np.concatenate([none, none, interest])
    )
    sim.reset_calculations()
    return interest, {
        variable: sim.calculate(variable, YEAR).astype(float).reshape(3, CASES)
        for variable in VARIABLES
    }


def tolerance(*values):
    """A penny plus float32 rounding on the amounts involved."""
    return 0.01 + 1e-6 * sum(np.abs(v) for v in values)


SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    database=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(amounts)
@example([2_000.0] * CASES)
def test_other_investment_income_counts_like_bank_interest(sim, drawn):
    interest, r = run(sim, drawn)
    # Income tax charges the two alike, and so does every income measure.
    for variable, (_, bank, other) in r.items():
        assert (np.abs(other - bank) <= tolerance(bank, other)).all(), variable
    # Market and capital income rise by the interest.
    for variable in ("market_income", "capital_income", "household_market_income"):
        none, _, other = r[variable]
        change = other - none
        assert (np.abs(change - interest) <= tolerance(other, interest)).all(), variable
    # Net income rises by the interest less the tax on it: it never falls.
    for variable in (
        "household_net_income",
        "hbai_household_net_income_before_reset_to_zero",
    ):
        none, _, other = r[variable]
        change = other - none
        margin = tolerance(other, none)
        assert (change >= -margin).all(), variable
        assert (change <= interest + margin).all(), variable

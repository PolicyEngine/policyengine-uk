"""Property tests for the Budget 2026 Pension Tax Allowance.

The allowance (paragraph 6.182; Table 6.1, item 52) is 20% of the full new
State Pension above the Personal Allowance, rounded up to the pound, tapered
by 1 for every 3 of total income above the full new State Pension, for people
over State Pension age or reaching it within the tax year, from 6 April 2027
to 5 April 2030. It is a reduction at Step 6 of the Income Tax calculation, so
it cannot take the tax below zero. Each test draws people and checks
identities that hold for every input:

- the allowance lies between zero and the tapered full allowance, so it is
  zero from three full allowances above the threshold;
- people who reach State Pension age after the tax year get nothing;
- Income Tax falls by exactly the allowance relative to the same law without
  it, and never goes below zero;
- the taper has no cliff edge: each extra pound of pension income takes at
  most a third of a pound off the allowance.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEARS = [2027, 2028, 2029]
CASES = 24
STEP = 25.0
PTA = "gov.hmrc.income_tax.reliefs.pension_tax_allowance"
WITHOUT_PTA = {f"{PTA}.in_effect": {str(year): False for year in YEARS}}
REGIONS = ["LONDON", "WALES", "NORTHERN_IRELAND", "SCOTLAND"]

amount = st.one_of(
    st.floats(min_value=0, max_value=20_000),
    st.floats(min_value=12_000, max_value=14_500),
    st.sampled_from([0.0, 12_570.0, 13_036.40, 13_318.40]),
)
case = st.tuples(
    st.sampled_from([60, 65, 66, 67, 70, 85]),  # age
    amount,  # State Pension
    amount,  # private pension
    st.one_of(st.just(0.0), amount),  # employment income
    st.one_of(st.just(0.0), st.floats(min_value=0, max_value=3_000)),  # savings
)
cases = st.lists(case, min_size=CASES, max_size=CASES)
years = st.sampled_from(YEARS)


def situation():
    # The second half repeats the first with STEP more private pension.
    n = 2 * CASES
    return {
        "people": {f"person_{i}": {} for i in range(n)},
        "benunits": {f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(n)},
        "households": {
            f"household_{i}": {
                "members": [f"person_{i}"],
                "region": {year: REGIONS[i % len(REGIONS)] for year in YEARS},
            }
            for i in range(n)
        },
    }


@pytest.fixture(scope="module")
def sims():
    return Simulation(situation=situation()), Simulation(
        situation=situation(), reform=WITHOUT_PTA
    )


VARIABLES = [
    "months_since_state_pension_age",
    "personal_allowance",
    "total_income",
    "income_tax_pre_charges",
    "pension_tax_allowance",
    "income_tax",
]


def run(sims, drawn, year):
    age, state_pension, private_pension, employment, savings = (
        np.tile(np.array(column), 2) for column in zip(*drawn)
    )
    private_pension[CASES:] += STEP
    results = []
    for sim in sims:
        sim.set_input("age", year, age)
        sim.set_input("state_pension", year, state_pension)
        sim.set_input("private_pension_income", year, private_pension)
        sim.set_input("employment_income", year, employment)
        sim.set_input("savings_interest_income", year, savings)
        sim.reset_calculations()
        results.append({v: sim.calculate(v, year).astype(float) for v in VARIABLES})
    return results


def full_allowance(sim, year):
    p = sim.tax_benefit_system.parameters.gov.hmrc.income_tax
    threshold = p.reliefs.pension_tax_allowance.state_pension_threshold(f"{year}-04-30")
    allowance = p.allowances.personal_allowance.amount(f"{year}-04-30")
    return threshold, np.ceil(round(0.2 * (threshold - allowance), 6))


def tolerance(*values):
    """A penny plus float32 rounding on the amounts involved."""
    return 0.01 + 1e-6 * sum(np.abs(v) for v in values)


SETTINGS = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(cases, years)
def test_allowance_lies_between_zero_and_the_tapered_full_allowance(sims, drawn, year):
    law, _ = run(sims, drawn, year)
    threshold, full = full_allowance(sims[0], year)
    pta = law["pension_tax_allowance"]
    excess = np.maximum(0, law["total_income"] - threshold)
    tapered = np.maximum(0, full - excess / 3)
    tol = tolerance(law["total_income"])
    assert full > 0
    assert (pta >= 0).all()
    assert (pta <= tapered + tol).all()
    assert (pta[excess >= 3 * full] == 0).all()


@SETTINGS
@given(cases, years)
def test_people_reaching_state_pension_age_after_the_year_get_nothing(
    sims, drawn, year
):
    law, _ = run(sims, drawn, year)
    later = law["months_since_state_pension_age"] <= -6
    assert (law["pension_tax_allowance"][later] == 0).all()


@SETTINGS
@given(cases, years)
def test_income_tax_falls_by_exactly_the_allowance(sims, drawn, year):
    law, without = run(sims, drawn, year)
    pta = law["pension_tax_allowance"]
    fall = without["income_tax"] - law["income_tax"]
    tol = tolerance(without["income_tax"])
    assert (law["income_tax"] >= 0).all()
    assert (np.abs(fall - pta) <= tol).all()
    assert (without["pension_tax_allowance"] == 0).all()


@SETTINGS
@given(cases, years)
def test_the_allowance_falls_by_at_most_a_third_of_extra_income(sims, drawn, year):
    law, _ = run(sims, drawn, year)
    pta = law["pension_tax_allowance"]
    base, more = pta[:CASES], pta[CASES:]
    # Capped at the tax due, which rises with income, the allowance can fall
    # no faster than the 1-in-3 taper: no cliff edge at the threshold or at
    # the point where the cap stops binding.
    assert (base - more <= STEP / 3 + 0.01).all()

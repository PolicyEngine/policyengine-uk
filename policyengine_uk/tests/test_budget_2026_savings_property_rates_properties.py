"""Property tests for the Budget 2026 savings and property income rates.

Budget 2026 adds 2 percentage points to the savings and property rates from
6 April 2027 (paragraphs 6.246 and 6.247), on top of Budget 2025's 22%, 42%
and 47%. Each test compares current law with the Budget 2025 rates for the
same generated people, and checks identities that hold for every input:

- rUK property tax rises by exactly 2% of taxable property income, since every
  pound of it sits in one of the three rate bands;
- Scottish taxpayers' property tax does not change, because their property
  income stays on the Scottish rates;
- savings tax rises by exactly 2% of the savings income in the basic, higher
  and additional bands, in every UK country;
- finance cost relief, which follows the property basic rate, never falls,
  and rises by at most 2% of the costs relieved wherever the Budget 2025
  relief was its full 22%. Where the tax left after earlier reductions
  capped it, the relief can rise by more: the higher rates leave more tax
  for it (test_capped_finance_cost_relief_can_rise_by_more_than_two_points).
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2027
RISE = 0.02
REGIONS = ["LONDON", "WALES", "NORTHERN_IRELAND", "SCOTLAND"]
CASES = 24
BUDGET_2025_RATES = {
    f"gov.hmrc.income_tax.rates.{source}.{band}": {str(YEAR): rate}
    for source in ("savings", "property")
    for band, rate in (("basic", 0.22), ("higher", 0.42), ("additional", 0.47))
}

amount = st.one_of(
    st.floats(min_value=0, max_value=60_000),
    st.floats(min_value=0, max_value=300_000),
    st.sampled_from([0.0, 1_000.0, 12_570.0, 37_700.0, 50_270.0, 125_140.0]),
)
case = st.tuples(
    amount,  # employment income
    amount,  # property profit
    st.floats(min_value=0, max_value=1),  # finance costs as a share of profit
    st.one_of(st.floats(min_value=0, max_value=20_000), amount),  # savings
)
cases = st.lists(case, min_size=CASES, max_size=CASES)


def situation():
    return {
        "people": {
            f"person_{i}": {"age": {YEAR: 45}, "employment_income": {YEAR: 0}}
            for i in range(CASES)
        },
        "benunits": {
            f"benunit_{i}": {"members": [f"person_{i}"]} for i in range(CASES)
        },
        "households": {
            f"household_{i}": {
                "members": [f"person_{i}"],
                "region": {YEAR: REGIONS[i % len(REGIONS)]},
            }
            for i in range(CASES)
        },
    }


@pytest.fixture(scope="module")
def sims():
    return Simulation(situation=situation()), Simulation(
        situation=situation(), reform=BUDGET_2025_RATES
    )


VARIABLES = [
    "pays_scottish_income_tax",
    "taxable_property_income_after_allowances",
    "property_income_tax",
    "savings_income_tax",
    "basic_rate_savings_income",
    "higher_rate_savings_income",
    "add_rate_savings_income",
    "property_finance_costs_relieved",
    "property_finance_cost_relief",
    "income_tax",
]


def run(sims, drawn):
    employment, profit, cost_share, savings = map(np.array, zip(*drawn))
    results = []
    for sim in sims:
        sim.set_input("employment_income", YEAR, employment)
        sim.set_input("property_income", YEAR, profit)
        sim.set_input("property_finance_costs", YEAR, profit * cost_share)
        sim.set_input("savings_interest_income", YEAR, savings)
        sim.reset_calculations()
        results.append({v: sim.calculate(v, YEAR).astype(float) for v in VARIABLES})
    return results


def tolerance(*values):
    """A penny plus float32 rounding on the amounts involved."""
    return 0.01 + 1e-6 * sum(np.abs(v) for v in values)


SETTINGS = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)


@SETTINGS
@given(cases)
def test_ruk_property_tax_rises_by_two_points_of_taxable_property(sims, drawn):
    law, before = run(sims, drawn)
    ruk = ~law["pays_scottish_income_tax"].astype(bool)
    rise = law["property_income_tax"] - before["property_income_tax"]
    expected = RISE * law["taxable_property_income_after_allowances"]
    tol = tolerance(law["property_income_tax"], expected)
    assert (np.abs(rise - expected)[ruk] <= tol[ruk]).all()


@SETTINGS
@given(cases)
def test_scottish_property_tax_ignores_the_property_rates(sims, drawn):
    law, before = run(sims, drawn)
    scottish = law["pays_scottish_income_tax"].astype(bool)
    rise = law["property_income_tax"] - before["property_income_tax"]
    tol = tolerance(law["property_income_tax"])
    assert (np.abs(rise)[scottish] <= tol[scottish]).all()


@SETTINGS
@given(cases)
def test_savings_tax_rises_by_two_points_in_every_country(sims, drawn):
    law, before = run(sims, drawn)
    banded = (
        law["basic_rate_savings_income"]
        + law["higher_rate_savings_income"]
        + law["add_rate_savings_income"]
    )
    rise = law["savings_income_tax"] - before["savings_income_tax"]
    tol = tolerance(law["savings_income_tax"], banded)
    assert (np.abs(rise - RISE * banded) <= tol).all()


@SETTINGS
@given(cases)
def test_finance_cost_relief_rises_by_at_most_two_points(sims, drawn):
    law, before = run(sims, drawn)
    rise = law["property_finance_cost_relief"] - before["property_finance_cost_relief"]
    cap = RISE * law["property_finance_costs_relieved"]
    tol = tolerance(law["property_finance_cost_relief"], cap)
    assert (rise >= -tol).all()
    full_before = 0.22 * before["property_finance_costs_relieved"]
    uncapped = np.abs(before["property_finance_cost_relief"] - full_before) <= tol
    assert (rise <= cap + tol)[uncapped].all()


def test_capped_finance_cost_relief_can_rise_by_more_than_two_points():
    """£7,800 of earlier tax credits leave £86 of tax under the Budget 2025
    rates, so the relief on £1,000 of finance costs is £86, not £220. The
    Budget 2026 rates raise tax before reductions by £400, to £8,286, leaving
    £486: the relief is its full 24%, £240, a rise of £154."""
    situation = {
        "people": {
            "person": {
                "age": {YEAR: 45},
                "employment_income": {YEAR: 30_000},
                "property_income": {YEAR: 20_000},
                "property_finance_costs": {YEAR: 1_000},
                "other_tax_credits": {YEAR: 7_800},
            }
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {
            "household": {"members": ["person"], "region": {YEAR: "LONDON"}}
        },
    }
    law = Simulation(situation=situation)
    before = Simulation(situation=situation, reform=BUDGET_2025_RATES)
    relief = "property_finance_cost_relief"
    assert float(before.calculate(relief, YEAR)[0]) == pytest.approx(86, abs=0.01)
    assert float(law.calculate(relief, YEAR)[0]) == pytest.approx(240, abs=0.01)
    assert float(before.calculate("income_tax", YEAR)[0]) == pytest.approx(0, abs=0.01)
    assert float(law.calculate("income_tax", YEAR)[0]) == pytest.approx(246, abs=0.01)

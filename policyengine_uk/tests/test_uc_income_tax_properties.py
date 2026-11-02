"""Property tests for the income tax that Universal Credit deducts from
earnings (uc_income_tax_on_earnings and uc_income_tax_on_trade).

The helper takes earnings as the lowest slice of non-savings income, after the
allowances set against non-savings income first, as PAYE codes set them
against the job. The least-tax share of the reliefs and allowances (ITA 2007
s. 25(2)) can move the allowances onto savings or dividends to lower the
year's tax, but the slice follows the order non-savings, savings, dividends,
so tax on other income never comes off earnings:

- adding savings or dividend income never raises either slice, for every
  person whose allowances it leaves unchanged (more income can taper the
  Personal Allowance, which raises the tax on earnings for a reason of its
  own).
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

PEOPLE = 8
YEARS = (2025, 2026, 2027, 2028)
REGIONS = ["LONDON", "SCOTLAND", "WALES", "NORTH_EAST"]
INCOMES = (
    "employment_income",
    "self_employment_income",
    "property_income",
    "savings_interest_income",
    "dividend_income",
    "trading_loss",
)
SLICES = ("uc_income_tax_on_earnings", "uc_income_tax_on_trade")

amount = st.one_of(
    st.just(0.0),
    st.floats(min_value=0, max_value=20_000),
    st.floats(min_value=0, max_value=80_000),
    st.sampled_from([5_000.0, 12_570.0, 37_406.0, 37_700.0, 50_270.0]),
)
person = st.tuples(*([amount] * len(INCOMES)))
extra = st.tuples(amount, amount)  # savings and dividends added
people = st.lists(st.tuples(person, extra), min_size=PEOPLE, max_size=PEOPLE)
# Self-employment income of £37,406: £14,407 of savings would move the whole
# Personal Allowance onto the savings under the least-tax share.
WITNESS = [((0.0, 37_406.0, 0.0, 0.0, 0.0, 0.0), (14_407.0, 0.0))] + [
    ((0.0,) * len(INCOMES), (0.0, 0.0))
] * (PEOPLE - 1)


def situation(year):
    return {
        "people": {f"p{i}": {"age": {year: 40}} for i in range(PEOPLE)},
        "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(PEOPLE)},
        "households": {
            f"h{i}": {
                "members": [f"p{i}"],
                "region": {year: REGIONS[i % len(REGIONS)]},
            }
            for i in range(PEOPLE)
        },
    }


@pytest.fixture(scope="module")
def sims():
    cache = {}

    def get(year):
        if year not in cache:
            cache[year] = Simulation(situation=situation(year))
        return cache[year]

    return get


def run(sim, year, incomes):
    for name, values in incomes.items():
        sim.set_input(name, year, np.asarray(values, dtype=float))
    sim.reset_calculations()
    return {
        name: sim.calculate(name, year).astype(float)
        for name in SLICES + ("allowances", "income_tax")
    }


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(st.sampled_from(YEARS), people)
@example(2025, WITNESS)
@example(2026, WITNESS)
def test_more_savings_or_dividends_never_raise_tax_on_earnings(sims, year, drawn):
    base_people, added = zip(*drawn)
    incomes = {
        name: np.array(values) for name, values in zip(INCOMES, zip(*base_people))
    }
    savings, dividends = (np.array(values) for values in zip(*added))
    sim = sims(year)
    before = run(sim, year, incomes)
    more = dict(incomes)
    more["savings_interest_income"] = incomes["savings_interest_income"] + savings
    more["dividend_income"] = incomes["dividend_income"] + dividends
    after = run(sim, year, more)
    same_allowances = np.abs(after["allowances"] - before["allowances"]) <= 0.01
    for name in SLICES:
        rise = after[name] - before[name]
        tolerance = 0.01 + 1e-6 * np.abs(before[name])
        assert (rise <= tolerance)[same_allowances].all(), (
            name,
            rise[same_allowances].max(),
        )


def test_savings_leave_the_tax_on_self_employment_unchanged(sims):
    """Self-employment income of £37,406, alone and with £14,407 of savings,
    in 2026-27. With the savings, the least-tax share sets the whole Personal
    Allowance against them, and income tax falls from £8,057.20 under the
    order non-savings, savings, dividends to £8,016. The tax on the trade
    stays at (37,406 - 12,570) x 20% = £4,967.20, as without the savings."""
    year = 2026
    sim = sims(year)
    zeros = np.zeros(PEOPLE)
    incomes = {name: zeros.copy() for name in INCOMES}
    incomes["self_employment_income"][0] = 37_406
    alone = run(sim, year, incomes)
    incomes["savings_interest_income"][0] = 14_407
    with_savings = run(sim, year, incomes)
    assert alone["uc_income_tax_on_trade"][0] == pytest.approx(4_967.2, abs=0.01)
    assert with_savings["uc_income_tax_on_trade"][0] == pytest.approx(4_967.2, abs=0.01)
    assert with_savings["uc_income_tax_on_earnings"][0] == pytest.approx(
        4_967.2, abs=0.01
    )
    assert with_savings["income_tax"][0] == pytest.approx(8_016, abs=0.01)

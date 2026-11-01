"""Property tests for setting Income Tax reliefs and allowances against income
in the way that gives the least tax (ITA 2007 s. 25(2) and, from 2027-28,
s. 25(3A); #2106).

The invariants, for every person without Marriage Allowance, on the Step 5
tax (income_tax_pre_charges), which is all the share changes:

1. Least tax: no share of the deductions between the components s. 25 lets
   them come off gives less Step 5 tax than the model's. A brute-force oracle
   forces each share on a grid through the model's own variables.
2. The tax never exceeds what the order non-savings, savings, dividends
   charges, which is the order the model used before #2106.
3. The deductions set against the components add up to the deductions used,
   min(relief + allowances, income), and none exceeds its component.
4. With one kind of income there is nothing to share, so the tax and the
   deductions are the old order's.
5. The search's own tax function agrees with income_tax_pre_charges on every
   share (a differential test of two implementations of Step 5).
6. The vertex search finds the least value of that function, checked against
   a dense grid.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.utils.income_tax_allocation import (
    _context,
    _least_tax_share,
    _shares,
    default_order_deductions,
    step_5_tax,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEARS = (2026, 2027)
PEOPLE = 8
REGIONS = ["LONDON", "SCOTLAND", "WALES", "NORTH_EAST"]
INCOMES = (
    "employment_income",
    "savings_interest_income",
    "dividend_income",
    "property_income",
    "trading_loss",
    "gift_aid",
)
ALLOCATION = (
    "received_allowances_earned_income",
    "received_allowances_savings_income",
    "received_allowances_dividend_income",
    "trade_loss_relief_against_savings_and_dividends",
)
VARIABLES = ALLOCATION + (
    "net_income_before_trade_loss_relief",
    "taxable_savings_interest_income",
    "taxable_dividend_income",
    "taxable_property_income",
    "trade_loss_relief_against_general_income",
    "allowances",
    "income_tax_pre_charges",
)
# Hand-built people for the brute-force oracle: (year, region, incomes).
HAND_BUILT = [
    (2026, "LONDON", dict(savings_interest_income=4_000, dividend_income=20_000)),
    (2026, "LONDON", dict(employment_income=50_000, savings_interest_income=10_000)),
    (2026, "LONDON", dict(employment_income=50_000, dividend_income=20_000)),
    (
        2026,
        "LONDON",
        dict(
            savings_interest_income=4_000, dividend_income=200_000, trading_loss=1_000
        ),
    ),
    (
        2027,
        "LONDON",
        dict(property_income=20_000, dividend_income=200_000, trading_loss=1_000),
    ),
    (
        2026,
        "SCOTLAND",
        dict(
            employment_income=3_000,
            savings_interest_income=4_000,
            dividend_income=20_000,
        ),
    ),
    (
        2027,
        "LONDON",
        dict(
            employment_income=9_000,
            property_income=30_000,
            savings_interest_income=6_000,
            dividend_income=15_000,
        ),
    ),
    (
        2026,
        "WALES",
        dict(
            employment_income=40_000,
            savings_interest_income=3_000,
            dividend_income=8_000,
            gift_aid=2_000,
        ),
    ),
]
GRID = 21

amount = st.one_of(
    st.just(0.0),
    st.floats(min_value=0, max_value=20_000),
    st.floats(min_value=0, max_value=150_000),
    st.sampled_from([4_000.0, 6_000.0, 12_570.0, 37_700.0, 50_270.0, 125_140.0]),
)
person = st.tuples(*([amount] * 5), st.floats(min_value=0, max_value=5_000))
people = st.lists(person, min_size=PEOPLE, max_size=PEOPLE)
year = st.sampled_from(YEARS)
SETTINGS = settings(
    max_examples=8,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def situation(count, year, regions):
    return {
        "people": {f"p{i}": {"age": {year: 40}} for i in range(count)},
        "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(count)},
        "households": {
            f"h{i}": {"members": [f"p{i}"], "region": {year: regions[i]}}
            for i in range(count)
        },
    }


@pytest.fixture(scope="module")
def sims():
    """Simulations built once and reused: one for the model's own share and
    one with the share forced, for each year and set of regions."""
    cache = {}

    def get(year, regions, forced=False):
        key = (year, tuple(regions), forced)
        if key not in cache:
            cache[key] = Simulation(situation=situation(len(regions), year, regions))
        return cache[key]

    return get


def run(sim, year, incomes, forced=None):
    count = sim.populations["person"].count
    for name in INCOMES:
        values = np.asarray(incomes.get(name, 0.0), dtype=float)
        sim.set_input(name, year, np.broadcast_to(values, (count,)).copy())
    for name, values in (forced or {}).items():
        sim.set_input(name, year, np.asarray(values, dtype=float))
    sim.reset_calculations()
    return sim


def results(sim, year):
    return {name: sim.calculate(name, year).astype(float) for name in VARIABLES}


def parameters_of(sim):
    return lambda period: sim.tax_benefit_system.parameters(str(period))


def draw(drawn):
    return {name: np.array(values) for name, values in zip(INCOMES, zip(*drawn))}


def tolerance(*values):
    """A penny plus float32 rounding on the amounts involved."""
    return 0.01 + 2e-7 * sum(np.abs(v) for v in values)


def default_order(sim, year):
    default = default_order_deductions(sim.populations["person"], year)
    return {
        "received_allowances_savings_income": default.savings,
        "received_allowances_dividend_income": default.dividends,
    }


@SETTINGS
@given(year, people)
@example(
    2026,
    [(0.0, 4_000.0, 20_000.0, 0.0, 0.0, 0.0), (50_000.0, 10_000.0, 0.0, 0.0, 0.0, 0.0)]
    + [(0.0,) * 6] * (PEOPLE - 2),
)
def test_least_tax_never_exceeds_default_order_and_adds_up(sims, year, drawn):
    incomes = draw(drawn)
    regions = [REGIONS[i % len(REGIONS)] for i in range(PEOPLE)]
    law_sim = run(sims(year, regions), year, incomes)
    law = results(law_sim, year)
    forced = run(sims(year, regions, True), year, incomes, default_order(law_sim, year))
    default = results(forced, year)

    # Invariant 2: never more tax than the order non-savings, savings, dividends.
    # The share changes only the Step 5 tax: the Step 6 reductions and Step 7
    # charges do not depend on it.
    tax, old_tax = law["income_tax_pre_charges"], default["income_tax_pre_charges"]
    assert np.all(tax <= old_tax + tolerance(old_tax)), (tax, old_tax)

    # Invariant 3: the deductions add up and none exceeds its component.
    savings = np.maximum(0, law["taxable_savings_interest_income"])
    dividends = np.maximum(0, law["taxable_dividend_income"])
    non_savings = np.maximum(
        0, law["net_income_before_trade_loss_relief"] - savings - dividends
    )
    relief = law["trade_loss_relief_against_general_income"]
    used = np.minimum(relief + law["allowances"], non_savings + savings + dividends)
    to_savings = law["received_allowances_savings_income"]
    to_dividends = law["received_allowances_dividend_income"]
    relief_left = law["trade_loss_relief_against_savings_and_dividends"]
    to_non_savings = law["received_allowances_earned_income"] + relief - relief_left
    margin = tolerance(used)
    assert np.all(np.abs(to_non_savings + to_savings + to_dividends - used) <= margin)
    for share, component in [
        (to_non_savings, non_savings),
        (to_savings, savings),
        (to_dividends, dividends),
    ]:
        assert np.all(share >= -margin) and np.all(share <= component + margin)
    assert np.all(relief_left <= relief + margin)
    assert np.all(relief_left <= to_savings + to_dividends + margin)

    # Invariant 4: one kind of income, nothing to share.
    kinds = (non_savings > 0).astype(int) + (savings > 0) + (dividends > 0)
    single = kinds <= 1
    np.testing.assert_allclose(tax[single], old_tax[single], atol=0.01)
    for name in ALLOCATION:
        np.testing.assert_allclose(law[name][single], default[name][single], atol=0.01)


@pytest.mark.parametrize(
    "year, region, incomes",
    HAND_BUILT,
    ids=[
        f"{year}-{region}-" + "-".join(incomes) for year, region, incomes in HAND_BUILT
    ],
)
def test_tax_equals_brute_force_grid_minimum(sims, year, region, incomes):
    law_sim = run(sims(year, [region]), year, incomes)
    law = results(law_sim, year)
    c = _context(law_sim.populations["person"], year, parameters_of(law_sim))
    savings, dividends = c.savings[0, 0], c.dividends[0, 0]
    used, non_savings = c.used[0, 0], c.non_savings[0, 0]
    # From 2027-28 s. 25(3A) sets the deductions against other income first.
    at_least_non_savings = used - c.shared[0, 0] if c.other_first else 0
    to_savings, to_dividends = (
        grid.ravel()
        for grid in np.meshgrid(
            np.linspace(0, min(savings, used), GRID),
            np.linspace(0, min(dividends, used), GRID),
        )
    )
    to_non_savings = used - to_savings - to_dividends
    feasible = (to_non_savings >= at_least_non_savings - 1e-6) & (
        to_non_savings <= non_savings + 1e-6
    )
    forced = run(
        sims(year, [region] * GRID**2, True),
        year,
        incomes,
        {
            "received_allowances_savings_income": to_savings,
            "received_allowances_dividend_income": to_dividends,
        },
    )
    grid_tax = forced.calculate("income_tax_pre_charges", year).astype(float)
    model_tax = law["income_tax_pre_charges"][0]
    least = grid_tax[feasible].min()
    step = min(savings, used) / (GRID - 1) + min(dividends, used) / (GRID - 1)
    # Invariant 1: the model's share is the least; the grid comes within its
    # step of it, since a pound moved between components changes the tax by
    # less than a pound.
    assert model_tax <= least + tolerance(model_tax)
    assert model_tax >= least - step - tolerance(model_tax)
    # Invariant 5: the search's tax function is the model's Step 5 tax.
    forced_c = _context(forced.populations["person"], year, parameters_of(forced))
    x = (forced_c.step_3_income - forced_c.savings - forced_c.dividends)[:, 0]
    x = x + to_savings + to_dividends
    s = savings - to_savings
    v = dividends - to_dividends
    own = step_5_tax(forced_c, x[:, None], s[:, None], v[:, None])[:, 0]
    np.testing.assert_allclose(
        own[feasible], grid_tax[feasible], atol=tolerance(grid_tax).max()
    )


@SETTINGS
@given(year, people)
def test_vertex_search_equals_dense_grid(sims, year, drawn):
    incomes = draw(drawn)
    regions = [REGIONS[i % len(REGIONS)] for i in range(PEOPLE)]
    sim = run(sims(year, regions), year, incomes)
    c = _context(sim.populations["person"], year, parameters_of(sim))
    x, s, v = _least_tax_share(c)
    found = step_5_tax(c, x, s, v)[:, 0]
    # Invariant 6: a 101 x 101 grid over the first component and savings
    # left, projected onto the feasible shares.
    total = c.step_3_income
    low = np.maximum(0, total - c.savings - c.dividends)
    high = np.minimum(c.first, total)
    fractions = np.linspace(0, 1, 101)
    grid_x = (low + (high - low) * fractions[None, :]).repeat(101, axis=1)
    grid_s = np.tile(c.savings * fractions[None, :], 101)
    grid_x, grid_s, grid_v = _shares(c, grid_x, grid_x + grid_s)
    grid = step_5_tax(c, grid_x, grid_s, grid_v).min(axis=1)
    step = ((high - low) / 100 + c.savings / 100)[:, 0]
    # The search may take a share within TIE (1e-6) of the least, for its
    # tie-break.
    assert np.all(found <= grid + 1e-5)
    assert np.all(found >= grid - 2 * step - 1e-5)

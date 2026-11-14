"""Property tests for setting Income Tax reliefs and allowances against income
in the way that gives the least tax (ITA 2007 s. 25(2) and, from 2027-28,
s. 25(3A); #2106).

The first seven invariants hold for every person with no Marriage Allowance
reduction at stake, on the Step 5 tax (income_tax_pre_charges), the only tax
the share then changes:

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
7. Fast path: for everyone the tests in _old_order_is_least let through, the
   result equals the full search's, bit for bit, and in current law those
   tests let through everyone with one kind of income.

The rest concern Marriage Allowance recipients, whose share also decides the
reduction at Step 6:

8. Income tax never exceeds what the order non-savings, savings, dividends
   charges.
9. No share forced through the model's own variables gives less income tax
   than the model's share.
10. Where the search moves a share and counts it as meeting the rate test, the
    model's own variables meet the test at that share, through float32 rounding.
    For every recipient the model's answer to the test is the one the search
    counted on: the test in float64 on the income the stored deductions leave,
    or in float32 as the model has always applied it.
11. The vertex search finds the least Step 5 tax less the reduction a share
    wins, checked against a dense grid and the thin sets on which the rate test
    can hold: no dividends left, and savings left at the savings allowance.
12. Fast path: invariant 7 holds with recipients among the people.
"""

from types import SimpleNamespace

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core import periods

from policyengine_uk import Simulation
from policyengine_uk.utils.income_tax_allocation import (
    _build,
    _context,
    _float32_meets_rate_test,
    _least_tax_share,
    _meets_rate_test,
    _old_order_is_least,
    _share_left,
    _shares,
    default_order_deductions,
    least_tax_deductions,
    old_order,
    step_5_tax,
    tax_after_marriage_allowance,
)
from policyengine_uk.utils.marriage_allowance import (
    marriage_allowance_rate_limits,
    meets_marriage_allowance_rate_test,
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
    # Invariant 1: the model's share gives the least tax; the grid comes within its
    # step of it, since a pound moved between components changes the tax by
    # less than a pound.
    assert model_tax <= least + tolerance(model_tax)
    assert model_tax >= least - step - tolerance(model_tax)
    # Invariant 5: the search's tax function equals the model's Step 5 tax.
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


# The fast path, checked on many synthetic people at once without a simulation:
# the inputs the search reads, drawn freely, and the old order computed from
# them as the model does, in float32.
SYNTHETIC_YEARS = tuple(range(2016, 2031))
SYNTHETIC_PEOPLE = 2_000
LIMITS = [500, 1_000, 5_000, 6_000, 12_570, 17_570, 37_700, 50_270, 100_000, 125_140]
# Curated people at the edges of each test: other non-savings income, property,
# savings, dividends, trade loss relief, allowances beyond the Personal
# Allowance, an exclusion from earned income, grossed-up Gift Aid, Scottish,
# and personal savings allowance.
EDGES = [
    # Pay and savings across the basic rate limit: the search moves £270.
    (50_000, 0, 10_000, 0, 0, 0, 0, 0, False, 500),
    # Pay and dividends across the basic rate limit.
    (50_000, 0, 0, 20_000, 0, 0, 0, 0, False, 500),
    # Pay that ends exactly at the basic rate limit, and a pound below it.
    (50_270, 0, 10_000, 0, 0, 0, 0, 0, False, 500),
    (50_269, 0, 10_000, 0, 0, 0, 0, 0, False, 500),
    # Savings and dividends with no other income.
    (0, 0, 4_000, 20_000, 0, 0, 0, 0, False, 1_000),
    # An exclusion from earned income moves the savings below the basic rate
    # limit.
    (51_000, 0, 10_000, 0, 0, 0, 1_260, 0, False, 500),
    (49_000, 0, 0, 20_000, 0, 0, 1_260, 0, False, 500),
    # Savings exactly at the savings allowance, dividends at the allowance.
    (30_000, 0, 1_000, 500, 0, 0, 0, 0, False, 1_000),
    (30_000, 0, 1_001, 501, 0, 0, 0, 0, False, 1_000),
    # Deductions that just fill the first component.
    (12_570, 0, 3_000, 0, 0, 0, 0, 0, False, 1_000),
    (12_570, 0, 3_000, 2_000, 0, 0, 0, 0, False, 1_000),
    # A pensioner whose savings fill the starting rate band.
    (14_000, 0, 8_000, 0, 0, 0, 0, 0, False, 1_000),
    # Scottish pay in the starter, basic and intermediate bands.
    (14_000, 0, 7_000, 0, 0, 0, 0, 0, True, 1_000),
    (25_000, 0, 2_000, 3_000, 0, 0, 0, 0, True, 1_000),
    (40_000, 0, 0, 5_000, 0, 0, 0, 0, True, 500),
    (43_000, 0, 6_000, 0, 0, 0, 0, 0, True, 500),
    # Property with other income, savings and dividends.
    (9_000, 30_000, 6_000, 15_000, 0, 0, 0, 0, False, 500),
    (9_000, 30_000, 6_000, 15_000, 0, 0, 0, 0, True, 500),
    # Scottish property income on 42% beside savings on 44% from 2027-28.
    (0, 58_000, 24_000, 0, 0, 0, 0, 0, True, 500),
    (0, 20_000, 0, 200_000, 1_000, 0, 0, 0, False, 0),
    (45_000, 20_000, 3_000, 0, 0, 0, 1_260, 0, False, 500),
    # Gift Aid raises the limits.
    (40_000, 0, 3_000, 8_000, 0, 0, 0, 2_000, False, 1_000),
    (52_000, 0, 9_000, 0, 0, 0, 0, 2_000, False, 500),
    # Pension relief and a trading loss.
    (60_000, 0, 9_000, 4_000, 3_000, 10_000, 0, 0, False, 500),
    (110_000, 0, 20_000, 30_000, 0, 0, 0, 0, False, 0),
    # A gift that lifts the UK limits above the £10 million extra bracket, so
    # the thresholds no longer ascend.
    (15_050_070, 0, 0, 10_000, 0, 12_570, 0, 15_000_000, False, 0),
]


@pytest.fixture(scope="module")
def system():
    import policyengine_uk.simulation as uk_simulation

    return uk_simulation.CountryTaxBenefitSystem()


def synthetic_people(
    seed, count=SYNTHETIC_PEOPLE, mix="free", exclusions=False, basic_rate_limit=37_700
):
    """Inputs for ``least_tax_deductions`` and the old order's deductions.

    "free" draws every amount from a wide mixture with values at the limits;
    "realistic" gives most people pay alone and some savings or dividends;
    "near-limit" puts income after the Personal Allowance just around the basic
    rate limit, where a share can win the Marriage Allowance.
    A tenth of the people get an exclusion from earned income of £1,260; with
    ``exclusions``, half get one of up to £20,000 instead."""
    rng = np.random.default_rng(seed)

    def amount(zero, scale):
        rest = 1 - zero
        kind = rng.choice(4, count, p=[zero, 0.3 * rest, 0.4 * rest, 0.3 * rest])
        limits = rng.choice(LIMITS, count) + rng.uniform(-300, 300, count)
        values = np.select(
            [kind == 0, kind == 1, kind == 2],
            [0, rng.uniform(0, 2_000, count), rng.uniform(0, scale, count)],
            limits,
        )
        return np.maximum(0, values)

    if mix == "free":
        other = amount(0.2, 200_000)
        property_income = amount(0.6, 60_000)
        savings = amount(0.4, 150_000)
        dividends = amount(0.5, 250_000)
    elif mix == "near-limit":
        savings = np.where(
            rng.random(count) < 0.5,
            rng.uniform(0, 1_200, count),
            rng.uniform(0, 12_570, count),
        )
        dividends = np.where(rng.random(count) < 0.5, 0, rng.uniform(0, 5_000, count))
        non_savings = np.maximum(
            0,
            basic_rate_limit
            + rng.uniform(-3, 900, count)
            + 12_570
            - savings
            - dividends,
        )
        property_income = np.where(rng.random(count) < 0.5, non_savings, 0)
        other = non_savings - property_income
    else:
        other = rng.lognormal(10.2, 0.6, count)
        property_income = np.where(
            rng.random(count) < 0.05, rng.uniform(0, 20_000, count), 0
        )
        savings = np.where(rng.random(count) < 0.25, rng.lognormal(5, 1.5, count), 0)
        dividends = np.where(rng.random(count) < 0.08, rng.lognormal(7, 1.5, count), 0)
    income = other + property_income + savings + dividends
    relief = np.where(
        rng.random(count) < 0.1, np.minimum(rng.uniform(0, 30_000, count), income), 0
    )
    extra = np.where(rng.random(count) < 0.2, rng.uniform(0, 15_000, count), 0)
    excluded = rng.random(count) < 0.1
    gift = np.where(rng.random(count) < 0.1, rng.uniform(0, 10_000, count), 0)
    scottish = rng.random(count) < 0.3
    savings_allowance = rng.choice([0.0, 500.0, 1_000.0], count)
    pension = np.where(rng.random(count) < 0.2, rng.uniform(0, 20_000, count), 0)
    exclusion_draw = np.where(rng.random(count) < 0.5, rng.uniform(0, 20_000, count), 0)
    rows = np.array(EDGES, dtype=float) if mix == "free" else np.empty((0, 10))
    other, property_income, savings, dividends, relief, extra, exclusion, gift = (
        np.concatenate([column, rows[:, i]])
        for i, column in enumerate(
            [
                other,
                property_income,
                savings,
                dividends,
                relief,
                extra,
                excluded * 1_260.0,
                gift,
            ]
        )
    )
    scottish = np.concatenate([scottish, rows[:, 8] > 0])
    savings_allowance = np.concatenate([savings_allowance, rows[:, 9]])
    pension = np.concatenate([pension, np.zeros(len(rows))])
    if exclusions:
        # A reform's exclusion from earned income, such as an exempt pension.
        exclusion = np.concatenate([exclusion_draw, rows[:, 6]])
    f32 = np.float32
    before_relief = (other + property_income + savings + dividends).astype(f32)
    relief = relief.astype(f32)
    net_income = np.maximum(0, before_relief - relief)
    personal_allowance = np.maximum(0, 12_570 - np.maximum(0, net_income - 100_000) / 2)
    allowances = (personal_allowance + extra + pension).astype(f32)
    savings, dividends = savings.astype(f32), dividends.astype(f32)
    default = old_order(
        allowances, savings, dividends, net_income, relief, before_relief
    )
    inputs = dict(
        savings=savings,
        dividends=dividends,
        relief=relief,
        net_income=net_income,
        property=property_income.astype(f32),
        allowances=allowances,
        pension=pension.astype(f32),
        earned_exclusions=exclusion.astype(f32),
        gift=gift.astype(f32),
        scottish=scottish,
        savings_allowance=savings_allowance.astype(f32),
    )
    inputs = {
        name: values if name == "scottish" else values.astype(np.float64)
        for name, values in inputs.items()
    }
    return inputs, default


def assert_fast_path_equals_search(income_tax, inputs, default):
    fast = least_tax_deductions(inputs, income_tax, default.savings, default.dividends)
    full = least_tax_deductions(
        inputs, income_tax, default.savings, default.dividends, search_all=True
    )
    for fast_part, full_part in zip(fast, full):
        mismatch = np.flatnonzero(fast_part != full_part)
        assert not len(mismatch), {
            name: values[mismatch[:5]] for name, values in inputs.items()
        }


@settings(
    max_examples=30,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(st.sampled_from(SYNTHETIC_YEARS), st.integers(0, 2**32 - 1))
@example(2025, 0)
@example(2026, 0)
@example(2027, 0)
@example(2028, 1)
def test_fast_path_equals_full_search(system, year, seed):
    income_tax = system.parameters(str(year)).gov.hmrc.income_tax
    inputs, default = synthetic_people(seed)
    # Invariant 7: the people the tests let through get the search's result.
    assert_fast_path_equals_search(income_tax, inputs, default)


@pytest.mark.parametrize("year", [2026, 2027])
def test_fast_path_lets_most_realistic_people_through(system, year):
    income_tax = system.parameters(str(year)).gov.hmrc.income_tax
    inputs, default = synthetic_people(2106, count=20_000, mix="realistic")
    c = _build(inputs, income_tax)
    through = _old_order_is_least(
        c, default.savings[:, None], default.dividends[:, None]
    )[:, 0]
    # With one kind of income nothing can move (invariant 4), so all of
    # those go through; and few of the rest need the search.
    one_kind = (inputs["savings"] == 0) & (inputs["dividends"] == 0)
    assert through[one_kind].all()
    assert (~through).mean() < 0.1, (~through).mean()


# Rates that fall with income break the arguments of tests 2 and 3, so the
# tests must then send everyone with something to share to the search.
FALLING_RATES = {
    "gov.hmrc.income_tax.rates.scotland.rates[3].rate": 0.05,
    "gov.hmrc.income_tax.rates.uk[1].rate": 0.1,
    "gov.hmrc.income_tax.rates.dividends[1].rate": 0.05,
}


@pytest.mark.parametrize("year", [2026, 2027])
def test_fast_path_equals_full_search_when_rates_fall(system, year):
    parameters = system.parameters
    old = {}
    try:
        for path, value in FALLING_RATES.items():
            parameter = parameters.get_child(path)
            old[path] = parameter(str(year))
            parameter.update(period=str(year), value=value)
        system.reset_parameter_caches()
        income_tax = parameters(str(year)).gov.hmrc.income_tax
        for seed in range(3):
            inputs, default = synthetic_people(seed)
            assert_fast_path_equals_search(income_tax, inputs, default)
    finally:
        for path, value in old.items():
            parameters.get_child(path).update(period=str(year), value=value)
        system.reset_parameter_caches()


def vertex_search_and_grid(income_tax, inputs, points=101):
    """The search's least Step 5 tax and a dense grid's least, per person,
    with the grid's step."""
    c = _build(inputs, income_tax)
    x, s, v = _least_tax_share(c)
    found = step_5_tax(c, x, s, v)[:, 0]
    total = c.step_3_income
    low = np.maximum(0, total - c.savings - c.dividends)
    high = np.minimum(c.first, total)
    fractions = np.linspace(0, 1, points)
    grid_x = (low + (high - low) * fractions[None, :]).repeat(points, axis=1)
    grid_s = np.tile(c.savings * fractions[None, :], points)
    grid_x, grid_s, grid_v = _shares(c, grid_x, grid_x + grid_s)
    grid = step_5_tax(c, grid_x, grid_s, grid_v).min(axis=1)
    step = ((high - low) / (points - 1) + c.savings / (points - 1))[:, 0]
    return found, grid, step


@pytest.mark.parametrize("year", [2018, 2026, 2027])
def test_vertex_search_equals_dense_grid_with_exclusions(system, year):
    """Invariant 6 on synthetic people with exclusions from earned income of
    up to £20,000 beside property income, as a reform that exempts pensions
    gives. Before 2027-28 the exclusion splits the first component into three
    pieces, each with its own lines."""
    income_tax = system.parameters(str(year)).gov.hmrc.income_tax
    for seed in range(2):
        inputs, _ = synthetic_people(seed, count=300, exclusions=True)
        found, grid, step = vertex_search_and_grid(income_tax, inputs)
        worst = np.argmax(found - grid)
        assert np.all(found <= grid + 1e-5), {
            name: values[worst] for name, values in inputs.items()
        } | {"found": found[worst], "grid": grid[worst]}
        assert np.all(found >= grid - 2 * step - 1e-5)


def one_person(**amounts):
    """``least_tax_deductions`` inputs for one person, and the old order's
    deductions, computed as the model computes them from net income and net
    income before trade loss relief."""
    values = dict(
        savings=0.0,
        dividends=0.0,
        relief=0.0,
        net_income=0.0,
        property=0.0,
        allowances=12_570.0,
        pension=0.0,
        earned_exclusions=0.0,
        gift=0.0,
        savings_allowance=1_000.0,
    )
    before_relief = amounts.pop("before_relief", None)
    scottish = amounts.pop("scottish", False)
    values.update(amounts)
    if before_relief is None:
        before_relief = values["net_income"] + values["relief"]
    inputs = {
        name: np.array([value], dtype=np.float64) for name, value in values.items()
    }
    inputs["scottish"] = np.array([scottish])
    f32 = np.float32
    default = old_order(
        *(
            np.array([value], dtype=f32)
            for value in (
                values["allowances"],
                values["savings"],
                values["dividends"],
                values["net_income"],
                values["relief"],
                before_relief,
            )
        )
    )
    return inputs, default


def tax_saved(income_tax, inputs, default):
    """The Step 5 tax under the old order less the tax under the full search's
    share, in the search's own tax function."""
    full = least_tax_deductions(
        inputs, income_tax, default.savings, default.dividends, search_all=True
    )
    c = _build(inputs, income_tax)

    def tax(to_savings, to_dividends):
        s = c.savings - np.asarray(to_savings, dtype=float)[:, None]
        v = c.dividends - np.asarray(to_dividends, dtype=float)[:, None]
        return step_5_tax(c, c.step_3_income - s - v, s, v)[0, 0]

    return tax(default.savings, default.dividends) - tax(*full)


@pytest.mark.parametrize(
    "amounts, saving",
    [
        # Savings of £1,000 the only income in net income before the relief,
        # with £1,000 of trade loss relief, and a supplied adjusted net income
        # that puts net income at £30,000. The old order sets the relief
        # against the savings and leaves £17,430 of non-savings income at
        # 20%; setting it against non-savings income instead leaves £16,430,
        # and the £1,000 savings allowance covers the savings: £200 less.
        (
            dict(savings=1_000, relief=1_000, net_income=30_000, before_relief=1_000),
            200,
        ),
        # Savings of £300 and £300 of relief, with net income supplied at
        # £13,070: the old order leaves £500 of non-savings income at 20%, the
        # search £200, with the savings in the savings allowance: £60 less.
        (dict(savings=300, relief=300, net_income=13_070, before_relief=300), 60),
    ],
    ids=["relief-against-savings", "all-savings-used"],
)
def test_fast_path_follows_a_supplied_net_income(system, amounts, saving):
    """Where a supplied adjusted net income sets net income apart from net
    income before trade loss relief less the relief, the old order can set
    relief against savings while non-savings income remains. The fast path
    must send those people to the search."""
    income_tax = system.parameters("2026").gov.hmrc.income_tax
    inputs, default = one_person(**amounts)
    assert tax_saved(income_tax, inputs, default) == pytest.approx(saving, abs=1e-6)
    assert_fast_path_equals_search(income_tax, inputs, default)


def test_fast_path_reads_the_scottish_starter_rate(system):
    """A reform that lifts the top of the Scottish starter band to £9,000,
    above the £5,000 starting rate limit for savings. A Scottish taxpayer with
    £18,570 of pay and £20,000 of savings: the old order leaves £6,000 of pay
    at the 19% starter rate, and the savings above it, past the starting rate
    band, bear 20%. Moving £3,000 of the allowance to savings takes the pay to
    £9,000 and saves 1% of £3,000, £30. The fast path must read the Scottish
    rate on the pay, not the UK basic rate."""
    parameters = system.parameters
    path = "gov.hmrc.income_tax.rates.scotland.rates[1].threshold"
    parameter = parameters.get_child(path)
    before = parameter("2026")
    try:
        parameter.update(period="2026", value=9_000)
        system.reset_parameter_caches()
        income_tax = parameters("2026").gov.hmrc.income_tax
        inputs, default = one_person(savings=20_000, net_income=38_570, scottish=True)
        assert tax_saved(income_tax, inputs, default) == pytest.approx(30, abs=1e-6)
        assert_fast_path_equals_search(income_tax, inputs, default)
    finally:
        parameter.update(period="2026", value=before)
        system.reset_parameter_caches()


def test_pension_relief_stays_on_non_savings_income(system):
    """Pay of £40,000 with £10,000 of pension relief and £30,000 of savings in
    2026-27. The relief stays on the pay: the employer deducts net pay
    contributions from employment income (FA 2004 s. 193(2)), and for relief
    at source Parliament raises the basic and higher rate limits instead
    (s. 192(4)). So only the £12,570 allowance moves, and every share keeps
    the savings allowance below the basic rate limit: the old order stands.
    Sharing the pension relief would put the pay at the limit and save
    £100."""
    income_tax = system.parameters("2026").gov.hmrc.income_tax
    inputs, default = one_person(
        savings=30_000,
        net_income=70_000,
        allowances=22_570,
        pension=10_000,
        savings_allowance=500,
    )
    full = least_tax_deductions(
        inputs, income_tax, default.savings, default.dividends, search_all=True
    )
    assert full[0][0] == 0
    assert tax_saved(income_tax, inputs, default) == 0
    shared = dict(inputs, pension=np.array([0.0]))
    assert tax_saved(income_tax, shared, default) == pytest.approx(100, abs=1e-6)


# Marriage Allowance recipients: each married to a partner with no income, so
# the partner's unused Personal Allowance funds the transfer.
COUPLE_INCOMES = (
    "employment_income",
    "savings_interest_income",
    "dividend_income",
    "property_income",
)
FORCED_SHARE = (
    "received_allowances_savings_income",
    "received_allowances_dividend_income",
)
COUPLE_GRID = 11
# Hand-built recipients: (year, region, (pay, savings, dividends, property)).
RECIPIENTS = [
    # The share wins the reduction: all dividends and most savings covered.
    (2026, "LONDON", (40_000, 9_000, 1_570, 0)),
    (2026, "LONDON", (49_870, 600, 200, 0)),
    (2026, "LONDON", (45_000, 300, 200, 5_000)),
    (2026, "LONDON", (49_000, 1_000, 500, 0)),
    # The Scottish limit on non-savings income falls below the basic rate limit.
    (2026, "SCOTLAND", (40_000, 9_000, 1_570, 0)),
    # From 2027-28 the allowances come off other income first (s. 25(3A)).
    (2027, "LONDON", (0, 9_000, 1_570, 40_000)),
    (2027, "LONDON", (9_000, 6_000, 1_500, 30_000)),
    # No share wins it: non-savings income alone exceeds the limit.
    (2026, "WALES", (60_000, 5_000, 0, 0)),
    # The old order already meets the test.
    (2026, "LONDON", (30_000, 400, 100, 0)),
]


def couple_situation(year, regions):
    people, benunits, households = {}, {}, {}
    for i, region in enumerate(regions):
        members = [f"recipient_{i}", f"partner_{i}"]
        people[members[0]] = {"age": {year: 40}}
        people[members[1]] = {"age": {year: 40}}
        benunits[f"benunit_{i}"] = {"members": members, "is_married": {year: True}}
        households[f"household_{i}"] = {"members": members, "region": {year: region}}
    return {"people": people, "benunits": benunits, "households": households}


@pytest.fixture
def couple_sims():
    """Simulations reused within a test and released after it: each holds its
    own copy of the system, about 130 MB."""
    cache = {}

    def get(year, regions, kind="law"):
        key = (year, tuple(regions), kind)
        if key not in cache:
            cache[key] = Simulation(situation=couple_situation(year, regions))
        return cache[key]

    return get


def run_couples(sim, year, rows, forced=None):
    """Set one (pay, savings, dividends, property) per recipient, and optionally
    force the recipients' deductions from savings and dividends."""
    count = sim.populations["person"].count
    columns = zip(*rows)
    for name, values in zip(COUPLE_INCOMES, columns):
        inputs = np.zeros(count)
        inputs[0::2] = values
        sim.set_input(name, year, inputs)
    for name, values in zip(FORCED_SHARE, forced or ()):
        inputs = np.zeros(count)
        inputs[0::2] = values
        sim.set_input(name, year, inputs)
    sim.reset_calculations()
    return sim


def check_recipients(couple_sims, year, regions, rows):
    """Invariants 8, 9 and 10 for one recipient a row."""
    count = len(rows)
    law = run_couples(couple_sims(year, regions), year, rows)
    person = law.populations["person"]
    default = default_order_deductions(person, year)
    law_tax = law.calculate("income_tax", year).astype(float)[0::2]
    margin = 0.01 + 1e-6 * np.array(rows, dtype=float).sum(axis=1)

    # Each recipient's shares forced through the model's own variables: a grid,
    # then the old order.
    c = _context(person, year, parameters_of(law))
    fractions = np.linspace(0, 1, COUPLE_GRID)
    to_savings = np.minimum(c.savings, c.used)[0::2, :] * fractions[None, :]
    to_dividends = np.minimum(c.dividends, c.used)[0::2, :] * fractions[None, :]
    grid_savings = to_savings.repeat(COUPLE_GRID, axis=1)
    grid_dividends = np.tile(to_dividends, COUPLE_GRID)
    to_first = c.used[0::2] - grid_savings - grid_dividends
    at_least = (c.used - c.shared)[0::2] if c.other_first else 0
    feasible = (to_first >= at_least - 1e-6) & (to_first <= c.non_savings[0::2] + 1e-6)
    size = COUPLE_GRID**2 + 1
    forced_savings = np.column_stack([grid_savings, default.savings[0::2]])
    forced_dividends = np.column_stack([grid_dividends, default.dividends[0::2]])
    forced = run_couples(
        couple_sims(
            year, [region for region in regions for _ in range(size)], "forced"
        ),
        year,
        [row for row in rows for _ in range(size)],
        (forced_savings.ravel(), forced_dividends.ravel()),
    )
    forced_tax = (
        forced.calculate("income_tax", year).astype(float)[0::2].reshape(count, -1)
    )
    # Invariant 8: never more income tax than the old order.
    old_tax = forced_tax[:, -1]
    assert np.all(law_tax <= old_tax + margin), (rows, law_tax, old_tax)
    # Invariant 9: no forced share gives less income tax.
    least = np.where(feasible, forced_tax[:, :-1], np.inf).min(axis=1)
    assert np.all(law_tax <= least + margin), (rows, law_tax, least)

    # Invariant 10: the model meets the test where the search counts on it.
    x, s, v = _least_tax_share(c)
    counted = _meets_rate_test(c, x, s, v)[:, 0]
    stored = (
        law.calculate("received_allowances_savings_income", year).astype(float),
        law.calculate("received_allowances_dividend_income", year).astype(float),
    )
    moved = (stored[0] != default.savings) | (stored[1] != default.dividends)
    meets = law.calculate("meets_marriage_allowance_income_conditions", year)
    assert meets[moved & counted].all()
    # And it gives the search's own answer at the share it stores: the test in
    # float64 from the stored amounts, or in float32 as the model has always
    # applied it (the old order's own answer where the share did not move).
    held = stored[0][:, None], stored[1][:, None]
    single = np.where(
        moved,
        _float32_meets_rate_test(c, *held)[:, 0],
        c.old_order_meets_rate_test[:, 0],
    )
    expected = _meets_rate_test(c, *_share_left(c, *held))[:, 0] | single
    assert np.array_equal(meets, expected)


@pytest.mark.parametrize("year", sorted({year for year, _, _ in RECIPIENTS}))
def test_recipient_share_gives_the_least_income_tax(couple_sims, year):
    regions = [region for y, region, _ in RECIPIENTS if y == year]
    rows = [row for y, _, row in RECIPIENTS if y == year]
    check_recipients(couple_sims, year, regions, rows)


recipient = st.tuples(amount, amount, amount, st.just(0.0) | amount)
recipients = st.lists(recipient, min_size=4, max_size=4)


@settings(
    SETTINGS,
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.data_too_large,
        HealthCheck.function_scoped_fixture,
    ],
)
@given(year, recipients)
def test_drawn_recipient_share_gives_the_least_income_tax(couple_sims, year, rows):
    check_recipients(couple_sims, year, REGIONS, rows)


def test_rate_test_survives_float32_rounding(couple_sims):
    """Invariant 10 on many recipients whose income ends near the limits, in
    amounts that float32 rounds. Dividends and savings at the point the test
    turns on, and the income at the basic rate limit, are where rounding could
    deny the search's share its reduction."""
    year = 2026
    count = 3_000
    rng = np.random.default_rng(2106)
    after_allowance = 37_700 + rng.uniform(-3, 900, count)
    savings = np.where(
        rng.random(count) < 0.5,
        rng.uniform(0, 1_200, count),
        rng.uniform(0, 12_570, count),
    )
    dividends = np.where(rng.random(count) < 0.5, 0, rng.uniform(0, 5_000, count))
    pay = np.maximum(0, after_allowance + 12_570 - savings - dividends)
    rows = list(zip(pay, savings, dividends, np.zeros(count)))
    law = run_couples(couple_sims(year, ["LONDON"] * count), year, rows)
    person = law.populations["person"]
    c = _context(person, year, parameters_of(law))
    default = default_order_deductions(person, year)
    x, s, v = _least_tax_share(c)
    counted = _meets_rate_test(c, x, s, v)[:, 0]
    moved = (
        law.calculate("received_allowances_savings_income", year) != default.savings
    ) | (
        law.calculate("received_allowances_dividend_income", year) != default.dividends
    )
    meets = law.calculate("meets_marriage_allowance_income_conditions", year)
    assert (moved & counted).sum() > 100
    assert meets[moved & counted].all()


def with_marriage_allowance(income_tax, year, inputs, default, seed):
    """``inputs`` with a reduction at stake for about half the people, the rate
    test's limits for them, and the old order's answer to the test, in float32
    as the model computes it (``_old_order_meets_rate_test``)."""
    rng = np.random.default_rng(seed)
    count = len(inputs["savings"])
    f32 = np.float32
    arrays = dict(
        gift_aid_grossed_up=inputs["gift"].astype(f32),
        pays_scottish_income_tax=inputs["scottish"],
        savings_allowance=inputs["savings_allowance"].astype(f32),
    )
    limits = marriage_allowance_rate_limits(
        lambda name, period: arrays[name], periods.period(year), income_tax
    )
    savings = inputs["savings"].astype(f32)
    dividends = inputs["dividends"].astype(f32)
    non_savings_left = np.maximum(
        0,
        inputs["net_income"].astype(f32)
        - savings
        - dividends
        - inputs["allowances"].astype(f32),
    )
    meets = meets_marriage_allowance_rate_test(
        non_savings_left,
        np.maximum(0, savings - default.savings),
        np.maximum(0, dividends - default.dividends),
        SimpleNamespace(
            non_savings=np.asarray(limits.non_savings).astype(f32),
            basic_rate=np.asarray(limits.basic_rate).astype(f32),
            starting=limits.starting,
            savings_allowance=limits.savings_allowance,
        ),
    )
    return inputs | dict(
        marriage_allowance_reduction=rng.choice([0.0, 2.0, 100.0, 252.0], count),
        rate_test_non_savings_limit=np.asarray(limits.non_savings, dtype=np.float64),
        rate_test_savings_allowance=np.broadcast_to(
            np.asarray(limits.savings_allowance, dtype=np.float64), (count,)
        ),
        old_order_meets_rate_test=meets,
    )


@settings(
    max_examples=30,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(st.sampled_from(SYNTHETIC_YEARS), st.integers(0, 2**32 - 1))
@example(2015, 0)
@example(2026, 0)
@example(2027, 0)
def test_fast_path_equals_full_search_with_marriage_allowance(system, year, seed):
    # Invariant 12.
    income_tax = system.parameters(str(year)).gov.hmrc.income_tax
    limit = income_tax.rates.uk.thresholds[1]
    for mix in ("free", "near-limit"):
        inputs, default = synthetic_people(seed, mix=mix, basic_rate_limit=limit)
        inputs = with_marriage_allowance(income_tax, year, inputs, default, seed)
        assert_fast_path_equals_search(income_tax, inputs, default)


@pytest.mark.parametrize("year", [2018, 2026, 2027])
def test_vertex_search_weighs_the_marriage_allowance(system, year):
    """Invariant 11. The share found is feasible and no point on a 101 x 101
    grid, or on the thin sets where the rate test can hold, beats it."""
    income_tax = system.parameters(str(year)).gov.hmrc.income_tax
    limit = income_tax.rates.uk.thresholds[1]
    wins = 0
    for seed, mix in [(0, "free"), (1, "near-limit"), (2, "near-limit")]:
        inputs, default = synthetic_people(
            seed, count=300, mix=mix, basic_rate_limit=limit
        )
        inputs = with_marriage_allowance(income_tax, year, inputs, default, seed)
        c = _build(inputs, income_tax)
        x, s, v = _least_tax_share(c)
        found = tax_after_marriage_allowance(c, x, s, v)[:, 0]
        total = c.step_3_income
        low = np.maximum(0, total - c.savings - c.dividends)
        high = np.minimum(c.first, total)
        assert np.all(x >= low - 1e-6) and np.all(x <= high + 1e-6)
        assert np.all(s >= -1e-6) and np.all(s <= c.savings + 1e-6)
        assert np.all(v >= -1e-6) and np.all(v <= c.dividends + 1e-6)
        fractions = np.linspace(0, 1, 101)[None, :]
        line_x = low + (high - low) * fractions
        grid_x = line_x.repeat(101, axis=1)
        grid_s = np.tile(c.savings * fractions, 101)
        all_x = np.concatenate([grid_x, line_x, line_x], axis=1)
        all_w = np.concatenate(
            [
                grid_x + grid_s,
                np.broadcast_to(total, line_x.shape),
                line_x + c.rate_test_savings_allowance,
            ],
            axis=1,
        )
        all_x, all_s, all_v = _shares(c, all_x, all_w)
        least = tax_after_marriage_allowance(c, all_x, all_s, all_v).min(axis=1)
        worst = np.argmax(found - least)
        assert np.all(found <= least + 1e-5), {
            name: values[worst] for name, values in inputs.items()
        } | {"found": found[worst], "least": least[worst]}
        # The reduction changes the answer for someone, or this test proves
        # nothing about it.
        step_5_alone = _build(
            inputs | dict(marriage_allowance_reduction=np.zeros(len(x))), income_tax
        )
        x_alone, s_alone, v_alone = _least_tax_share(step_5_alone)
        wins += np.sum(
            np.abs(s[:, 0] - s_alone[:, 0]) + np.abs(v[:, 0] - v_alone[:, 0]) > 1
        )
    assert wins > 0


def test_search_keeps_a_recipient_the_test_passes_exactly_at_the_limit(system):
    """Pay of £38,570 and savings of £11,700 in 2026-27. The old order leaves
    £26,000 of pay and £37,700 in all, exactly the basic rate limit, which the
    rate test allows (s. 10(2)): 7,340 less the £252 reduction, 7,088. A share
    that stops savings at the £1,000 savings allowance gives the same 7,088, so
    the search must keep the old order rather than move the recipient for no saving."""
    income_tax = system.parameters("2026").gov.hmrc.income_tax
    inputs, default = one_person(savings=11_700, net_income=50_270)
    inputs = with_marriage_allowance(income_tax, 2026, inputs, default, 0)
    inputs["marriage_allowance_reduction"] = np.array([252.0])
    assert inputs["old_order_meets_rate_test"][0]
    to_savings, to_dividends = least_tax_deductions(
        inputs, income_tax, default.savings, default.dividends, search_all=True
    )
    assert to_savings[0] == 0 and to_dividends[0] == 0


def test_search_moves_a_person_whose_first_component_has_no_room(system):
    """Savings of £5,500 and dividends of £700.07 in 2026-27, with £3,569.63 of
    allowances and no non-savings income. The old order sets the allowances
    against savings, which leaves £1,930.37 of savings in the starting rate
    band and £700.07 of dividends: £200.07 above the £500 dividend allowance
    at 10.75%, £21.51. Setting £200.07 against the dividends and the rest
    against savings leaves £2,130.44 of savings in the band and the dividends
    within the allowance: nil.

    With no non-savings income the first component has no room, so the two
    deductions must add up to £3,569.63, which no float32 rounding of
    £3,369.56 does exactly. The search still moves the person."""
    income_tax = system.parameters("2026").gov.hmrc.income_tax
    inputs, default = one_person(
        savings=5_500, dividends=700.07, allowances=3_569.63, net_income=6_200.07
    )
    for search_all in (False, True):
        to_savings, to_dividends = least_tax_deductions(
            inputs, income_tax, default.savings, default.dividends, search_all
        )
        assert to_dividends[0] == pytest.approx(200.07, abs=1e-3)
        assert to_savings[0] + to_dividends[0] == pytest.approx(3_569.63, abs=1e-3)
    assert tax_saved(income_tax, inputs, default) == pytest.approx(21.51, abs=0.01)


def test_search_moves_a_recipient_with_no_property_income_from_2027(couple_sims):
    """Married recipients in 2027-28 whose partners have no income, with no
    property income, so the first component has no room.

    Pay £5,000, savings £2,000.37, dividends £20,000.11: net income £27,000.48,
    Step 3 income £14,430.48. Section 25(3A) takes £5,000 of the £12,570
    Personal Allowance off pay, and the taxpayer shares the other £7,570
    (s. 25(2)). The old order leaves dividends of £14,430.48, taxed at 10.75%
    above the £500 allowance: £1,497.53, less the £252 reduction, £1,245.53.
    Setting all £7,570 against the dividends leaves the savings in the starting
    rate band and dividends of £12,430.11: £1,282.49, less £252, £1,030.49.
    The other rows follow the same way."""
    year = 2027
    rows = [
        (5_000, 2_000.37, 20_000.11, 0),
        (5_000.13, 2_000.37, 20_000.11, 0),
        (9_000, 300.37, 10_485.76, 0),
        (9_000, 3.37, 10_485.76, 0),
    ]
    sim = run_couples(couple_sims(year, ["LONDON"] * len(rows)), year, rows)
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax == pytest.approx([1_030.49, 1_030.50, 437.69, 437.69], abs=0.01)


def explicit_couples(year, rows):
    """A Simulation of married recipients whose partners have no income, one
    couple a row. Each row maps person variables to the recipient's amounts,
    with ``region`` for the household."""
    people, benunits, households = {}, {}, {}
    for i, row in enumerate(rows):
        amounts = dict(row)
        region = amounts.pop("region", "LONDON")
        people[f"r{i}"] = {"age": {year: 40}, "uses_property_allowance": {year: False}}
        people[f"r{i}"] |= {name: {year: value} for name, value in amounts.items()}
        people[f"p{i}"] = {"age": {year: 40}}
        benunits[f"b{i}"] = {"members": [f"r{i}", f"p{i}"], "is_married": {year: True}}
        households[f"h{i}"] = {
            "members": [f"r{i}", f"p{i}"],
            "region": {year: region},
        }
    return Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )


# Whole-pence recipients in 2026-27, each a penny over a limit of the rate test
# under every share, so the law gives none of them the reduction. The model
# sums net income and allowances in float32, which puts some of them a fraction
# of a penny under the limit; the test must still fail them.
PENNY_OVER = [
    dict(
        employment_income=46_951.24,
        private_pension_income=1_366.33,
        property_income=646.47,
        savings_interest_income=166.71,
        dividend_income=1_305.97,
    ),
    dict(
        employment_income=46_699.33,
        private_pension_income=1_000.33,
        property_income=1_000.33,
        savings_interest_income=200.08,
        dividend_income=1_570.02,
    ),
    dict(
        employment_income=53_997.58,
        savings_interest_income=24.33,
        dividend_income=1_588.58,
        other_deductions=5_316.15,
    ),
    dict(
        employment_income=48_944.49,
        savings_interest_income=6_399.67,
        dividend_income=320.74,
        other_deductions=4_894.89,
    ),
    dict(
        employment_income=44_718.49,
        savings_interest_income=491.15,
        dividend_income=667.15,
        other_deductions=1_056.48,
        region="SCOTLAND",
    ),
    dict(
        employment_income=51_279.33,
        savings_interest_income=50.97,
        dividend_income=942.58,
        gift_aid=1_561.52,
    ),
    dict(
        employment_income=10_964.47,
        savings_interest_income=2_969.9,
        dividend_income=42_854.58,
        trading_loss=6_518.94,
    ),
]


def test_rate_test_fails_a_recipient_a_penny_over_a_limit():
    """Pay £53,997.58, savings £24.33, dividends £1,588.58 and other deductions
    of £5,316.15 (the third row): allowances of £17,886.15 leave £37,724.34, so
    the old order leaves dividends above the basic rate limit, and setting the
    £1,588.58 against the dividends leaves pay of £37,700.01, a penny over. The
    second row's tax, worked by hand without the reduction, is £7,391.05."""
    year = 2026
    sim = explicit_couples(year, PENNY_OVER)
    reduction = sim.calculate("marriage_allowance_tax_reduction", year)[0::2]
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    assert not meets.any() and not reduction.any()
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax[1] == pytest.approx(7_391.05, abs=0.01)


def test_rate_test_lets_income_reach_the_basic_rate_limit():
    """Pay £6,214.61, savings £367.26, dividends £47,955.74 and other deductions
    of £4,267.61 in 2026-27: allowances of £16,837.61 leave £37,700.00, the
    basic rate limit. Setting all £16,837.61 against pay and dividends, none
    against savings, leaves the savings in the starting rate band and dividends
    of £37,332.74, all the income at the limit: 10.75% above the £500
    allowance, £3,959.52,
    less the £252 reduction, £3,707.52. The old order leaves the dividends at
    £37,700, £3,999 less £252: £3,747."""
    year = 2026
    sim = explicit_couples(
        year,
        [
            dict(
                employment_income=6_214.61,
                savings_interest_income=367.26,
                dividend_income=47_955.74,
                other_deductions=4_267.61,
            )
        ],
    )
    assert sim.calculate("meets_marriage_allowance_income_conditions", year)[0]
    tax = sim.calculate("income_tax", year).astype(float)[0]
    assert tax == pytest.approx(3_707.52, abs=0.01)


def test_search_keeps_the_rounding_that_meets_the_rate_test_at_a_gift_aid_limit():
    """Pay £188.28, property income £121.87, savings £175.31, dividends
    £52,212.12, other deductions £1,218.28 and a Gift Aid gift of £967.44 in
    2028-29. Allowances of £13,788.28 leave £38,909.30, the basic rate limit
    raised by the £1,209.30 grossed-up gift (s. 414(2)(b)). Setting £310.15
    against pay and property income and £13,478.13 against dividends leaves
    savings in the starting rate band and dividends of £38,733.99, all the
    income at the limit: 10.75% above the £500 allowance, £4,110.15, less the
    £252 reduction, £3,858.15. Of the float32 roundings of that share, only
    the one that leaves the first component a fraction of a penny below nil
    meets the rate test."""
    year = 2028
    sim = explicit_couples(
        year,
        [
            dict(
                employment_income=188.28,
                property_income=121.87,
                savings_interest_income=175.31,
                dividend_income=52_212.12,
                other_deductions=1_218.28,
                gift_aid=967.44,
            )
        ],
    )
    assert sim.calculate("meets_marriage_allowance_income_conditions", year)[0]
    tax = sim.calculate("income_tax", year).astype(float)[0]
    assert tax == pytest.approx(3_858.15, abs=0.01)


def test_rate_test_fails_a_rounding_that_sets_more_than_the_shared_allowances():
    """Two 2026-27 recipients whose Gift Aid gifts raise the basic rate limit
    above their pay. The first: pay £157,600, savings £140,500.3125, other
    deductions £139,000, a trading loss of £1,000.30 and a gift of £96,000,
    which lifts the limit to £157,700 (s. 414(2)(b)). The Personal Allowance
    tapers to nil, so the shared amount is £139,000 plus £1,000.30 of loss
    relief, and every share leaves income of £158,100.0125: at least 1.25p
    of savings above the £500 savings nil rate band that starts at £157,600.
    So no share meets the rate test, and the tax is £31,520. Rounding the
    deduction from savings up to float32 would set 1.25p more than the shared
    amount against savings and leave them at the band. The second does the
    same with a step of 3.125p: pay £307,600, savings £301,500.03125, other
    deductions £300,000, a loss of £1,000.001 and a gift of £216,000. The
    third is the first with a loss of £1,000.3055, which leaves 0.7p of
    savings above the band. There the float32 value nearest the deduction
    from savings sets 0.7p more than the shared amount; in 2026-27 nothing
    rounds the shared amount, so that rounding ranks last too."""
    year = 2026
    common = dict(uses_trading_allowance=False)
    sim = explicit_couples(
        year,
        [
            dict(
                employment_income=157_600,
                savings_interest_income=140_500.3125,
                other_deductions=139_000,
                trading_loss=1_000.30,
                gift_aid=96_000,
                **common,
            ),
            dict(
                employment_income=307_600,
                savings_interest_income=301_500.03125,
                other_deductions=300_000,
                trading_loss=1_000.001,
                gift_aid=216_000,
                **common,
            ),
            dict(
                employment_income=157_600,
                savings_interest_income=140_500.3125,
                other_deductions=139_000,
                trading_loss=1_000.3055,
                gift_aid=96_000,
                **common,
            ),
        ],
    )
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    assert not meets.any()
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax == pytest.approx([31_520, 61_520, 31_520], abs=0.01)


@pytest.mark.parametrize(
    "year, row, expected",
    [
        (
            2027,
            dict(
                employment_income=19_149.97,
                savings_interest_income=218_144.28,
                dividend_income=0.29,
                other_deductions=197_220.30,
                gift_aid=1_899.40,
            ),
            7_925.75,
        ),
        (
            2028,
            dict(
                employment_income=43_314.39,
                savings_interest_income=212_622.26,
                dividend_income=1_182.93,
                other_deductions=219_419.59,
            ),
            7_145.51,
        ),
    ],
)
def test_search_keeps_the_nearest_rounding_where_net_income_rounds_up(
    year, row, expected
):
    """Scottish recipients whose other deductions exceed their pay, so from
    2027-28 the deductions take all the pay first (s. 25(3A)) and the rest
    falls on savings. In 2028-29: savings of £212,622.26 less £176,105.20
    leave £36,517.06, and with £1,182.93 of dividends income comes to
    £37,699.99, a penny inside the £37,700 basic rate limit. The tax is
    £30,517.06 × 24% on savings above the £5,000 starting rate band and the
    £1,000 savings allowance, plus £682.93 × 10.75% on dividends above the
    £500 dividend allowance: £7,397.51, or £7,145.51 after the £252
    reduction. In 2027-28 a £1,899.40 gift raises the limit to £40,074.25 and
    income comes to £40,074.24: £34,073.95 × 24% = £8,177.75, or £7,925.75.
    The model sums net income in float32 a fraction of a penny high, which
    puts income at the limit and shrinks the shared amount. Only the nearest
    float32 rounding of the deduction from savings meets the rate test, and
    against the model's shared amount it sets 0.7p more."""
    sim = explicit_couples(year, [dict(row, region="SCOTLAND")])
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    assert meets.all()
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax == pytest.approx([expected], abs=0.01)

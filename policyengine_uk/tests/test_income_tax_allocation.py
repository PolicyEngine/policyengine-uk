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
    The test also checks that the model's answer for every recipient is the one
    the search priced the stored share with (``_rate_test_on_stored``). That
    check restates the variable's formula, so it guards the wiring between the
    variable and the search, not the law.
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
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.utils.income_tax_allocation import (
    LOW_PRECISION,
    RATE_TEST_ROOM,
    RATE_TEST_ROOM_FRACTION,
    TIE,
    _build,
    _can_hide_an_excess,
    _context,
    _float32_meets_rate_test,
    _held_error,
    _inputs,
    _least_tax_share,
    _meets_rate_test,
    _old_order_is_least,
    _rate_test_on_stored,
    _share_left,
    _shares,
    _stored_share,
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
from policyengine_uk.utils.supplied_inputs import set_model_value

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


def test_rate_test_on_stored_counts_shares_that_meet_the_test_only_in_float64(
    system,
):
    """Two 2026-27 recipients whose pay, savings and dividends come to £50,270,
    so after the £12,570 Personal Allowance every share leaves income at the
    £37,700 basic rate limit, which meets the rate test (s. 10(2)). The model
    holds each amount in float32. For pay of £37,401.34, savings of £5,081.08
    and dividends of £7,787.58, the old order sets the allowance against pay.
    Taking the savings and dividends from net income in float32 leaves
    £24,831.34375 of pay, so the float32 test reads £37,700.0039 and fails. For
    pay of £32,747.81, savings of £7,271.86 and dividends of £10,250.33, a share
    that sets £6,771.86 against savings and £5,798.14 against dividends leaves
    £500 of savings. Summing what it leaves in float32 gives £37,700.0039 too.
    On the amounts the model holds, each share leaves £37,700 in float64, so
    ``_rate_test_on_stored`` counts both."""
    income_tax = system.parameters("2026").gov.hmrc.income_tax
    single = np.float32

    def context(pay, savings, dividends):
        held = [single(amount) for amount in (pay, savings, dividends)]
        inputs, default = one_person(
            net_income=float((held[0] + held[1]) + held[2]),
            savings=float(held[1]),
            dividends=float(held[2]),
        )
        inputs = with_marriage_allowance(income_tax, 2026, inputs, default, 0)
        return _build(inputs, income_tax), default

    c, default = context(37_401.34, 5_081.08, 7_787.58)
    old = (default.savings[:, None], default.dividends[:, None])
    assert not c.old_order_meets_rate_test[0, 0]
    assert _rate_test_on_stored(c, *old, np.array([[False]]))[0, 0]

    c, _ = context(32_747.81, 7_271.86, 10_250.33)
    moved = (np.array([[single(6_771.86)]]), np.array([[single(5_798.14)]]))
    assert not _float32_meets_rate_test(c, *moved)[0, 0]
    assert _rate_test_on_stored(c, *moved, np.array([[True]]))[0, 0]


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


def explicit_couples(year, rows, reform=None):
    """A Simulation of married recipients whose partners have no income, one
    couple a row. Each row maps person variables to the recipient's amounts,
    with ``region`` for the household. ``reform`` is a structural reform to
    build the simulation with."""
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
        situation={"people": people, "benunits": benunits, "households": households},
        reform=reform,
    )


# Whole-pence recipients in 2026-27, each a penny over a limit of the rate test
# under every share, so the law gives none of them the reduction. The model
# sums net income and allowances in float32, which leaves them 0.2p to 0.5p
# over the limit, not a whole penny; the test must still fail them.
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


# Whole-pence recipients in 2026-27 whose pay, savings and dividends come to
# £50,270. After the £12,570 Personal Allowance the old order leaves income at
# the £37,700 basic rate limit, so the law gives the reduction (s. 10(2)). The
# model holds the amounts in float32, and the float32 test reads income
# £0.0039 over the limit. The last row has a penny more of dividends, so the
# law denies it.
AT_THE_LIMIT_IN_FLOAT64 = [
    dict(
        employment_income=37_401.34,
        savings_interest_income=5_081.08,
        dividend_income=7_787.58,
    ),
    dict(
        employment_income=38_696.41,
        savings_interest_income=3_144.24,
        dividend_income=8_429.35,
    ),
    dict(
        employment_income=37_401.34,
        savings_interest_income=5_081.08,
        dividend_income=7_787.59,
    ),
]


def test_rate_test_reads_the_old_order_in_float64_too():
    """The first row's tax, worked by hand: £24,831.34 of pay at 20%, £4,081.08
    of savings above the £1,000 savings allowance at 20%, and £7,287.58 of
    dividends above the £500 dividend allowance at 10.75%: £6,565.90, or
    £6,313.90 after the £252 reduction. ``main`` denies it. In the last row the
    penny over the limit cuts the savings allowance to £500 (s. 12B), and the
    tax is £6,665.90."""
    year = 2026
    sim = explicit_couples(year, AT_THE_LIMIT_IN_FLOAT64)
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    assert meets.tolist() == [True, True, False]
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax[[0, 2]] == pytest.approx([6_313.90, 6_665.90], abs=0.01)


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
    £252 reduction, £3,858.15.

    The model sums net income to £52,697.58203125, 0.2p over the amounts
    entered, and holds the grossed-up gift as £1,209.2999267578125. So it
    holds Step 3 income 0.18p over the limit, and no share meets the rate
    test in float64. The float32 value nearest the deduction from dividends,
    £13,478.12890625, leaves the first component a fraction of a penny below
    nil. The float32 amounts it leaves sum to £38,909.30078125, the float32
    value of the limit, so it meets the test in float32 alone
    (``_rate_test_on_stored``). The next float32 value up fails the test in
    both arithmetics. A rounding that passes only in float32 ranks last
    where the exact share fails in float64, but not the nearest rounding, so
    ``_stored_share`` keeps it. The two tests below pin each step on the
    amounts the model holds, so a change in the parameters that moves the
    float32 tie fails them rather than this test's expected tax alone."""
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


def gift_aid_limit_context(system):
    """The search's context for the recipient of the test above, from the
    amounts the model holds for them: net income as the model sums it, the
    grossed-up gift as the model holds it, and the rest in float32."""
    income_tax = system.parameters("2028").gov.hmrc.income_tax
    single = np.float32
    inputs, default = one_person(
        net_income=52_697.58203125,
        savings=float(single(175.31)),
        dividends=float(single(52_212.12)),
        property=float(single(121.87)),
        allowances=float(single(13_788.28)),
        gift=1_209.2999267578125,
    )
    inputs = with_marriage_allowance(income_tax, 2028, inputs, default, 0)
    inputs["marriage_allowance_reduction"] = np.array([252.0])
    return _build(inputs, income_tax)


def test_rate_test_on_stored_counts_a_moved_share_that_meets_the_test_only_in_float32(
    system,
):
    """The Gift Aid recipient above. The model holds Step 3 income of
    £38,909.3017578125 against a limit of £38,909.29992675781, so the share
    that sets £13,478.12890625 against dividends fails the rate test in
    float64. In float32 the amounts it leaves sum to the float32 value of the
    limit, and the test passes. ``_rate_test_on_stored`` counts a moved share
    that meets the test in either arithmetic, so it counts this one."""
    c = gift_aid_limit_context(system)
    over = c.step_3_income[0, 0] - c.bands[1][0, 0]
    assert over == pytest.approx(0.0018, abs=1e-4)
    moved = (np.array([[0.0]]), np.array([[13_478.12890625]]))
    assert not _meets_rate_test(c, *_share_left(c, *moved))[0, 0]
    assert _float32_meets_rate_test(c, *moved)[0, 0]
    assert _rate_test_on_stored(c, *moved, np.array([[True]]))[0, 0]


def test_stored_share_keeps_the_nearest_rounding_that_meets_the_test_only_in_float32(
    system,
):
    """The Gift Aid recipient above. The share with the least ``f`` sets
    £13,478.1293 against dividends and fails the rate test in float64, as
    every share does. The float32 value nearest that deduction meets the
    test in float32 alone. A rounding that passes only in float32 ranks last
    where the exact share fails, unless it is the nearest, so
    ``_stored_share`` keeps this one and counts the £252 reduction: an ``f``
    of £3,858.15. The other rounding fails the test and leaves £4,110.15."""
    c = gift_aid_limit_context(system)
    _, s, v = _least_tax_share(c)
    exact = (c.savings - s, c.dividends - v)
    assert not _meets_rate_test(c, *_share_left(c, *exact))[0, 0]
    stored = _stored_share(c, s, v)
    assert stored.to_savings[0, 0] == 0
    assert stored.to_dividends[0, 0] == np.float32(exact[1][0, 0])
    assert stored.to_dividends[0, 0] == 13_478.12890625
    held = (stored.to_savings, stored.to_dividends)
    assert not _meets_rate_test(c, *_share_left(c, *held))[0, 0]
    assert _float32_meets_rate_test(c, *held)[0, 0]
    assert stored.tax[0, 0] == pytest.approx(3_858.15, abs=0.01)


def test_rate_test_fails_a_rounding_that_sets_more_than_the_shared_allowances():
    """Two 2026-27 recipients whose Gift Aid gifts raise the basic rate
    limit above their pay. The first: pay £157,600, savings £140,500.3125,
    other deductions £139,000, a trading loss of £1,000.30 and a gift of
    £96,000, which lifts the limit to £157,700 (s. 414(2)(b)). The Personal
    Allowance tapers to nil, so the shared amount is £139,000 plus £1,000.30
    of loss relief, and every share leaves income of £158,100.0125: at least
    1.25p of savings above the £500 savings nil rate band that starts at
    £157,600. So no share meets the rate test, and the tax is £31,520.005.
    Rounding the deduction from savings up to float32 would set 1.25p more
    than the shared amount against savings and leave them at the band. The
    second does the same with a step of 3.125p: pay £307,600, savings
    £301,500.03125, other deductions £300,000, a loss of £1,000.001 and a gift
    of £216,000 leave 3.03p of savings above the band and tax of £61,520.01.
    In both, the rounding that would pass is not the float32 value nearest
    the deduction, so it ranks last."""
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
        ],
    )
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    assert not meets.any()
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax == pytest.approx([31_520.005, 61_520.01], abs=0.01)


def test_search_keeps_a_rounding_within_half_a_penny_of_the_shared_allowances():
    """A 2027-28 recipient with no non-savings income: savings of £4,025.26,
    dividends of £52,610.04 and other deductions of £6,365.30. Allowances of
    £18,935.30 leave £37,700, the basic rate limit, so the law gives the
    reduction (s. 10(2)). The savings sit in the starting rate band at 0%, so
    the whole £18,935.30 goes against the dividends and leaves £33,674.74 of
    them: 10.75% above the £500 allowance, £3,566.28, or £3,314.28 after the
    £252 reduction. With no property income the two deductions must take the
    whole shared amount, and float32 cannot hold the deduction from dividends.
    The nearest value, £18,935.298828125, leaves income over the limit;
    ``main`` stores it and charges £3,566.29. The next value up,
    £18,935.30078125, sets 0.08p more than the shared amount, within
    ``OVER_DEDUCTION``, and meets the rate test, so the search keeps it."""
    year = 2027
    sim = explicit_couples(
        year,
        [
            dict(
                savings_interest_income=4_025.26,
                dividend_income=52_610.04,
                other_deductions=6_365.30,
            )
        ],
    )
    assert sim.calculate("meets_marriage_allowance_income_conditions", year)[0]
    to_dividends = sim.calculate("received_allowances_dividend_income", year)[0]
    assert to_dividends == 18_935.30078125
    tax = sim.calculate("income_tax", year).astype(float)[0]
    assert tax == pytest.approx(3_314.28, abs=0.01)


def test_search_ranks_last_a_rounding_more_than_half_a_penny_beyond_the_allowances(
    system,
):
    """Amounts as float32 holds them for a 2026-27 taxpayer with no Marriage
    Allowance at stake and no non-savings income: savings of £3,000, dividends
    of £400,000, other deductions of £139,000 and a trading loss of
    £1,000.30. The savings sit in the starting rate band at 0%, so the whole
    £140,000.30 of deductions goes against the dividends. Float32 holds that
    deduction as £140,000.296875, 0.3p under, or £140,000.3125, 1.25p over.
    The value above leaves 1.56p less of the dividends to tax at 39.35%, which
    saves more than ``TOLERANCE``. It sets more than ``OVER_DEDUCTION`` beyond
    the deductions and is not the nearest value, so it ranks last and the
    search stores the value below."""
    income_tax = system.parameters("2026").gov.hmrc.income_tax
    single = np.float32
    relief = single(1_000.30)
    net_income = single(403_000) - relief
    inputs, default = one_person(
        net_income=float(net_income),
        savings=3_000.0,
        dividends=400_000.0,
        allowances=139_000.0,
        relief=float(relief),
        before_relief=403_000.0,
    )
    for search_all in (False, True):
        to_savings, to_dividends = least_tax_deductions(
            inputs, income_tax, default.savings, default.dividends, search_all
        )
        assert to_savings[0] == 0
        assert to_dividends[0] == 140_000.296875


def test_search_keeps_the_nearest_rounding_where_stored_savings_sit_over_the_band():
    """2026-27 recipients whose £96,000 Gift Aid gifts raise the basic rate
    limit to £157,700 (s. 414(2)(b)), above their pay of £157,600. The first
    has savings of £140,500.01, other deductions of £139,000 and a trading
    loss of £1,000.01. The Personal Allowance tapers to nil, and setting the
    whole £140,000.01 of shared deductions against savings leaves £500 of
    them, at the top of the savings nil rate band. So the share meets the rate
    test, and the tax is £157,600 × 20% = £31,520, or £31,268 after the £252
    reduction. The model holds the savings in float32 as £140,500.015625, so
    the exact share leaves them 0.56p over the band. Only the float32 value
    nearest the deduction from savings, 0.56p over the shared amount, puts
    them back on it, and that rounding keeps its rank. The second and third
    are the first with a loss of £1,000.3055 and savings of £140,500.3125 and
    £140,500.305. The law leaves the second 0.7p of savings over the band and
    denies it the reduction, but gives the third the reduction. Both hold the
    same float32 amounts, so the model gives both the third's tax."""
    year = 2026
    common = dict(
        employment_income=157_600,
        other_deductions=139_000,
        gift_aid=96_000,
        uses_trading_allowance=False,
    )
    sim = explicit_couples(
        year,
        [
            dict(savings_interest_income=140_500.01, trading_loss=1_000.01, **common),
            dict(
                savings_interest_income=140_500.3125,
                trading_loss=1_000.3055,
                **common,
            ),
            dict(
                savings_interest_income=140_500.305,
                trading_loss=1_000.3055,
                **common,
            ),
        ],
    )
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    assert meets.all()
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax[1] == tax[2]
    assert tax == pytest.approx([31_268, 31_268, 31_268], abs=0.01)


def test_search_ranks_last_a_rounding_that_passes_only_in_float32():
    """A 2027-28 recipient with pay of £8,999.58, savings of £43,451.58,
    dividends of £3,696.72 and other deductions of £5,877.87. Allowances of
    £18,447.87 leave £37,700.01, a penny over the basic rate limit. The pay
    takes £8,999.58 of them first (s. 25(3A)), and the other £9,448.29 falls on
    savings and dividends, so a penny of them stays above the limit under
    every share and the law gives no reduction. Setting the £9,448.29 against
    savings leaves £34,003.29 of them: £28,503.29 above the £5,000 starting
    rate band and the £500 savings allowance at the model's 24%, £6,840.79.
    Of the dividends, £3,196.70 above the £500 allowance bear 10.75% and the
    last penny 35.75%: £343.65. That comes to £7,184.44. The model holds
    income 0.3p over the limit. The float32 value a step above the deduction
    from savings passes the float32 test alone. It is not the nearest value,
    so it ranks last, and the model denies the reduction, as ``main`` does."""
    year = 2027
    sim = explicit_couples(
        year,
        [
            dict(
                employment_income=8_999.58,
                savings_interest_income=43_451.58,
                dividend_income=3_696.72,
                other_deductions=5_877.87,
            )
        ],
    )
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    assert not meets.any()
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax == pytest.approx([7_184.44], abs=0.01)


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
    falls on savings. The savings basic rate is the model's 24% from 2027-28,
    which adds Budget 2026's announced rise to the 22% Parliament has set. In
    2028-29: savings of £212,622.26 less £176,105.20
    leave £36,517.06, and with £1,182.93 of dividends income comes to
    £37,699.99, a penny inside the £37,700 basic rate limit. The tax is
    £30,517.06 × 24% on savings above the £5,000 starting rate band and the
    £1,000 savings allowance, plus £682.93 × 10.75% on dividends above the
    £500 dividend allowance: £7,397.51, or £7,145.51 after the £252
    reduction. In 2027-28 a £1,899.40 gift raises the limit to £40,074.25 and
    income comes to £40,074.24: £34,073.95 × 24% = £8,177.75, or £7,925.75.
    The model sums net income in float32 0.69p high in 2027-28 and 1.375p
    high in 2028-29, which puts income at the limit and shrinks the shared
    amount. Only the nearest float32 rounding of the deduction from savings
    meets the rate test, and against the model's shared amount it sets 0.7p
    more. As the nearest rounding, it keeps its rank."""
    sim = explicit_couples(year, [dict(row, region="SCOTLAND")])
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    assert meets.all()
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax == pytest.approx([expected], abs=0.01)


def test_search_keeps_the_nearest_rounding_that_puts_income_on_the_limit():
    """A 2026-27 recipient with no non-savings income: savings £3,000.01,
    dividends £175,700, other deductions £140,000 and a trading loss of
    £1,000.01. The Personal Allowance tapers to nil, and the whole £141,000.01
    of shared deductions goes against the dividends, since the savings sit in
    the starting rate band for savings at 0%. That leaves Step 3 income of
    £37,700, at the basic rate limit, so the share meets the rate test. The
    tax is £34,199.99 × 10.75% on dividends above the £500 dividend
    allowance, £3,676.50, or £3,424.50 after the £252 reduction. The nearest
    float32 value of the deduction from dividends sets 0.56p more than the
    model's shared amount, and the rounding down leaves income over the
    limit. The nearest rounding keeps its rank, so the model gives the
    reduction."""
    year = 2026
    sim = explicit_couples(
        year,
        [
            dict(
                savings_interest_income=3_000.01,
                dividend_income=175_700,
                other_deductions=140_000,
                trading_loss=1_000.01,
                uses_trading_allowance=False,
            )
        ],
    )
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    assert meets.all()
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax == pytest.approx([3_424.50], abs=0.01)


def test_search_stores_the_nearest_rounding_of_a_deduction_off_the_float32_grid():
    """Two 2026-27 recipients with no non-savings income and shared deductions
    off the float32 grid. The first: savings £3,000, dividends £400,000, other
    deductions £300,000 and a trading loss of £1,000.02. The whole £301,000.02
    goes against the dividends, and float32 storage rounds it to
    £301,000.03125, 1.1p more. The model keeps that nearest value rather than
    the rounding down, which would tax 2p more of the dividends at 35.75%.
    The law's tax is £34,200 × 10.75% plus £64,299.98 × 35.75%: £26,663.74.

    The second has other deductions of £99,000 and a loss of £1,000.30. The
    nearest float32 value of the £100,000.30 is £100,000.296875, 0.3p under.
    The value above, £100,000.3046875, sets 0.47p more than the deductions,
    within ``OVER_DEDUCTION``, and would save 0.3p of tax. With dividends over
    £65,536, the search stores the nearest value for a recipient, as ``main``
    does. The law's tax is £34,200 × 10.75%, £87,440 × 35.75% and £177,859.70
    × 39.35%: £104,924.09."""
    year = 2026
    common = dict(
        savings_interest_income=3_000,
        dividend_income=400_000,
        uses_trading_allowance=False,
    )
    sim = explicit_couples(
        year,
        [
            dict(other_deductions=300_000, trading_loss=1_000.02, **common),
            dict(other_deductions=99_000, trading_loss=1_000.30, **common),
        ],
    )
    to_dividends = sim.calculate("received_allowances_dividend_income", year)[0::2]
    assert to_dividends.tolist() == [301_000.03125, 100_000.296875]
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax == pytest.approx([26_663.74, 104_924.09], abs=0.01)


@pytest.mark.parametrize(
    "amounts, low_precision",
    [
        # Every amount under £65,536.
        (dict(net_income=65_535.99), False),
        (dict(net_income=50_770.0, relief=14_765.99), False),
        (dict(net_income=40_000.0, gift=27_835.5), False),
        # Net income, and net income before the trade loss relief.
        (dict(net_income=65_536.0), True),
        (dict(net_income=50_770.0, relief=26_859.03), True),
        # The allowances, savings, dividends and an exclusion from earned income.
        (dict(net_income=40_000.0, allowances=65_536.0), True),
        (dict(net_income=40_000.0, savings=65_536.0), True),
        (dict(net_income=40_000.0, dividends=65_536.0), True),
        (dict(net_income=40_000.0, earned_exclusions=65_536.0), True),
        # A gift that raises the basic rate limit to £65,536.
        (dict(net_income=40_000.0, gift=27_836.0), True),
    ],
)
def test_rate_test_keeps_room_where_an_amount_reaches_65_536(
    system, amounts, low_precision
):
    """From £65,536 float32 holds amounts in steps of 0.78p or more, and can
    hold income entered a penny over a limit at the limit. So where any amount
    the rate test reads reaches £65,536, the test's limits sit below the
    statutory ones by the room ``main``'s search keeps: £0.001 plus a millionth
    of the limit or of the income after the deductions, whichever is more.
    Under £65,536 the limits are the statutory ones (plus ``TIE``)."""
    assert LOW_PRECISION == 65_536
    income_tax = system.parameters("2026").gov.hmrc.income_tax
    inputs, default = one_person(**amounts)
    inputs = with_marriage_allowance(income_tax, 2026, inputs, default, 0)
    c = _build(inputs, income_tax)
    assert c.low_precision[0, 0] == low_precision
    limit = 37_700 + inputs["gift"][0]
    room = RATE_TEST_ROOM + RATE_TEST_ROOM_FRACTION * max(
        limit, abs(c.step_3_income[0, 0])
    )
    expected = limit - room if low_precision else limit + TIE
    assert c.rate_test_limits.non_savings[0, 0] == pytest.approx(expected, abs=1e-9)
    assert c.rate_test_limits.basic_rate[0, 0] == pytest.approx(expected, abs=1e-9)


def test_rate_test_denies_a_penny_over_the_limit_that_float32_cannot_hold():
    """A 2026-27 recipient with pay of £190,529.99, savings of £9,000.02,
    dividends of £1,570, a trading loss of £50,275 and a Gift Aid gift of
    £80,044 (#2913, review of 6788c8e39). The loss fits the cap of s. 24A, a
    quarter of £201,100.01. The gift grosses up to £100,055, so adjusted net
    income is £50,770.01, the Personal Allowance stays £12,570, and the basic
    rate limit rises to £137,755 (ss. 58 and 414(2)(b)). Income after the
    allowance is £138,255.01, a penny over that limit plus the £500 savings
    allowance, so no share meets the rate test. The least tax leaves £500 of
    savings and £500 of dividends at their nil rates and £137,255.01 of pay at
    20%: £27,451.00.

    Float32 holds pay of £190,529.99 as £190,529.984375, and the model sums
    net income to £150,825, a penny under. So the model holds income of
    £138,255 after the allowance, the limit plus the savings allowance, and a
    search that let income reach the limit gave this recipient the £252
    reduction. Pay of £190,529.98 stores as the same float32 value. For that
    pay the law gives the reduction and charges £27,299. The model cannot
    tell the two apart, and denies both, as ``main`` does."""
    year = 2026
    common = dict(
        savings_interest_income=9_000.02,
        dividend_income=1_570,
        trading_loss=50_275,
        gift_aid=80_044,
    )
    sim = explicit_couples(
        year,
        [
            dict(employment_income=190_529.99, **common),
            dict(employment_income=190_529.98, **common),
        ],
    )
    reduction = sim.calculate("marriage_allowance_tax_reduction", year)[0::2]
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    assert not meets.any() and not reduction.any()
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax == pytest.approx([27_451.00, 27_451.00], abs=0.005)


# Whole-pence recipients in 2026-27, each a penny over a limit of the rate test
# under every share, with an amount of £65,536 or more. Float32 hides the penny
# and the model holds each at the limit. The law gives none of them the
# reduction, and neither does ``main``. Each row ends with the law's tax, to
# the penny.
PENNY_OVER_AT_LOW_PRECISION = [
    # Net income of £201,100.07 less £162,900.06 of other deductions leaves
    # £38,200.01, a penny over £37,700 plus the £500 savings allowance: £500 of
    # savings and of dividends at their nil rates, £37,200.01 of pay at 20%.
    (
        dict(
            employment_income=200_000.07,
            savings_interest_income=500,
            dividend_income=600,
            other_deductions=162_900.06,
        ),
        7_440.00,
    ),
    # As above, 2p over: £37,200.02 of pay at 20%.
    (
        dict(
            employment_income=300_000.14,
            savings_interest_income=500,
            dividend_income=600,
            other_deductions=262_900.12,
        ),
        7_440.00,
    ),
    # Pay over £131,072, and net income under it after a £30,000 trade loss:
    # £120,825.01. A £56,044 gift raises the limit to £107,755, and income
    # after the Personal Allowance is £108,255.01: £107,255.01 of pay at 20%.
    (
        dict(
            employment_income=140_254.99,
            savings_interest_income=9_000.02,
            dividend_income=1_570,
            trading_loss=30_000,
            gift_aid=56_044,
        ),
        21_451.00,
    ),
    # Every amount under £65,536 but their sum: pay, savings and dividends
    # come to £77,629.04, and a £26,859.03 trade loss leaves net income of
    # £50,770.01, which the model holds as £50,770. Income after the Personal
    # Allowance is £38,200.01: £37,200.01 of pay at 20%.
    (
        dict(
            employment_income=53_360.11,
            savings_interest_income=23_554.02,
            dividend_income=714.91,
            trading_loss=26_859.03,
        ),
        7_440.00,
    ),
    # A £78,284.20 gift raises the basic rate limit to £135,555.25. Net income
    # of £148,625.26 less the Personal Allowance is £136,055.26, a penny over
    # the limit plus £500: £135,055.26 of pay at 20%, £27,011.05.
    (
        dict(
            employment_income=140_426.63,
            savings_interest_income=7_683.60,
            dividend_income=515.03,
            gift_aid=78_284.20,
        ),
        27_011.05,
    ),
    # A Scottish taxpayer. A £70,206.24 gift raises the Scottish higher rate
    # threshold to £118,849.80 and the intermediate rate threshold to
    # £104,713.80. Pay less the Personal Allowance and a £2,721.20 trade loss
    # is £118,849.81, so a penny bears the higher rate: £3,967 at 19%,
    # £100,746.80 at 20%, £14,136 at 21% and 1p at 42%, £23,871.65. The savings
    # and dividends fall within their nil rates.
    (
        dict(
            employment_income=134_141.01,
            savings_interest_income=465.02,
            dividend_income=26.60,
            trading_loss=2_721.20,
            gift_aid=70_206.24,
            region="SCOTLAND",
        ),
        23_871.65,
    ),
    # Dividends that the £66,323.33 of deductions cannot clear. The deductions
    # take all £21,095.11 of pay and £45,228.22 of the dividends, and leave
    # £37,700.01 of them: £37,200 above the £500 allowance at 10.75% and a
    # penny at 35.75%, £3,999.00. The old order's deductions, as float32 holds
    # them, leave the dividends 0.39p over the limit, and the float32 value a
    # step above them leaves the dividends at it. A search that moved the
    # share by that step, for the 0.1p of tax it saves, won the reduction.
    (
        dict(
            employment_income=21_095.11,
            dividend_income=82_928.23,
            other_deductions=20_605.56,
            trading_loss=33_147.77,
            uses_trading_allowance=False,
        ),
        3_999.00,
    ),
    # A penny of savings over the savings nil rate band under every share
    # (pay × 20% plus 1p × 40%). A £56,111.20 gift raises the limit to
    # £107,839, above the pay.
    (
        dict(
            employment_income=107_739.11,
            savings_interest_income=46_884.52,
            other_deductions=33_687.92,
            trading_loss=126.59,
            gift_aid=56_111.20,
            uses_trading_allowance=False,
        ),
        21_547.83,
    ),
]


def test_rate_test_denies_a_penny_over_a_limit_at_low_precision():
    """Each recipient above sits a penny (the second, 2p) over a limit, and
    the model holds each at the limit. With an amount of £65,536 or more, the
    rate test keeps room below each limit, and the search decides and stores
    the share as ``main`` does, so the model gives none of them the reduction
    and charges the law's tax."""
    year = 2026
    rows = [row for row, _ in PENNY_OVER_AT_LOW_PRECISION]
    sim = explicit_couples(year, rows)
    reduction = sim.calculate("marriage_allowance_tax_reduction", year)[0::2]
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    assert not meets.any() and not reduction.any()
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    law_tax = [amount for _, amount in PENNY_OVER_AT_LOW_PRECISION]
    assert tax == pytest.approx(law_tax, abs=0.01)


def test_rate_test_denies_a_penny_over_a_limit_at_low_precision_from_2027():
    """A 2027-28 recipient with pay of £13,251.08, property income of
    £43,099.65, savings of £31,948.22, dividends of £540.48 and other
    deductions of £38,069.42. Net income is £88,839.43, and allowances of
    £50,639.42 leave £38,200.01, a penny over the basic rate limit plus the
    £500 savings allowance, so no share meets the rate test. The pay takes
    £13,251.08 of the allowances first (s. 25(3A)). The least tax leaves £500
    of savings and £500 of dividends at their nil rates and £37,200.01 of
    property income at the model's 24%: £8,928.00. The model sums net income
    to £88,839.421875, 0.8p under, and holds income at the limit plus £500.
    Net income is over £65,536, so the rate test keeps room and the model
    denies the reduction, as ``main`` does."""
    year = 2027
    sim = explicit_couples(
        year,
        [
            dict(
                employment_income=13_251.08,
                property_income=43_099.65,
                savings_interest_income=31_948.22,
                dividend_income=540.48,
                other_deductions=38_069.42,
            )
        ],
    )
    assert not sim.calculate("meets_marriage_allowance_income_conditions", year)[0]
    assert sim.calculate("marriage_allowance_tax_reduction", year)[0] == 0
    tax = sim.calculate("income_tax", year).astype(float)[0]
    assert tax == pytest.approx(8_928.00, abs=0.01)


def test_search_stores_the_nearest_rounding_at_low_precision():
    """A 2027-28 recipient with pay of £53,841.65, savings of £141,016.82,
    dividends of £17,661.55, other deductions of £174,818.25 and a trading
    loss of £1.77. The Personal Allowance tapers to nil, and Step 3 income is
    £37,700, the basic rate limit, so the law gives the reduction and charges
    £4,962.09. The deductions take all the pay first (s. 25(3A)), and with no
    property income the other £120,978.37 falls on savings and dividends. The
    least tax sets it against savings. The model holds that amount midway
    between two float32 values. The nearest,
    £120,978.359375, leaves income 0.39p over the limit. The other sets 0.39p
    more than the shared amount and puts income on the limit. Savings and
    deductions sit over £65,536, so the rate test keeps room, the search
    stores the nearest value and the model denies the reduction, as ``main``
    does: £14,038.46 of savings above
    the starting rate band and the savings allowance at 24%, £3,369.23, and
    £17,161.55 of dividends above their allowance at 10.75%, £1,844.87."""
    year = 2027
    sim = explicit_couples(
        year,
        [
            dict(
                employment_income=53_841.65,
                savings_interest_income=141_016.82,
                dividend_income=17_661.55,
                other_deductions=174_818.25,
                trading_loss=1.77,
                uses_trading_allowance=False,
            )
        ],
    )
    assert not sim.calculate("meets_marriage_allowance_income_conditions", year)[0]
    to_savings = sim.calculate("received_allowances_savings_income", year)[0]
    assert to_savings == 120_978.359375
    tax = sim.calculate("income_tax", year).astype(float)[0]
    assert tax == pytest.approx(5_214.10, abs=0.01)


def test_search_finds_the_share_at_the_limit_less_the_room():
    """A Scottish recipient in 2027-28 with pay of £41,941.71, property income
    of £33,570.74, savings of £21,500, other deductions of £33,208.09 and a
    trading loss of £19,142.37. Net income of £77,870.08 less allowances of
    £45,778.09 leaves £32,091.99. The deductions take all the pay first
    (s. 25(3A)), and the other £22,978.75 falls on property income and
    savings. Savings above the £1,000 savings allowance bear the model's 24%,
    and property income under the Scottish higher rate threshold of £31,092
    bears 21% at most. So the least tax leaves as much property income as the
    rate test allows. Net income is over £65,536, so the test keeps 3.9p of
    room under the threshold. The share that leaves £31,091.96 of property
    income and £1,000.03 of savings lies on the line the search adds at the
    limit less the room, and it sets £20,499.96 against savings. Without that
    line the search sets £20,000 against savings, which leaves £500 more of
    savings at 24% and £500 less of property income at 21%, and the tax is
    £15 more. The test pins the share and not the tax, since the model
    projects the Scottish starter and basic rate thresholds for 2027-28."""
    year = 2027
    sim = explicit_couples(
        year,
        [
            dict(
                employment_income=41_941.71,
                property_income=33_570.74,
                savings_interest_income=21_500,
                other_deductions=33_208.09,
                trading_loss=19_142.37,
                uses_trading_allowance=False,
                region="SCOTLAND",
            )
        ],
    )
    assert sim.calculate("meets_marriage_allowance_income_conditions", year)[0]
    to_savings = sim.calculate("received_allowances_savings_income", year)[0]
    assert to_savings == 20_499.96484375
    property_left = sim.calculate("non_savings_income_after_allowances", year)[0]
    assert property_left == pytest.approx(31_092 - 0.0387, abs=0.01)


# Whole-pence recipients in 2026-27, each a penny over a limit of the rate test
# under every share (the last three, a quarter of a penny). The penny hides
# behind an amount the rate test does not read: every amount the test reads
# sits under £65,536, and the model holds each recipient at the limit. The law
# gives none of them the reduction, and neither does ``main``. Each row ends
# with the law's tax, to the penny.
PENNY_HIDDEN_BEHIND_THE_INCOME_TESTED = [
    # Pay less expenses of £40,200.01. With £9,000 of savings and £1,570 of
    # dividends, the Personal Allowance leaves £38,200.01, a penny over £37,700
    # plus the £500 savings allowance: £500 of savings and of dividends at
    # their nil rates and £37,200.01 at 20%. Float32 holds pay of £148,609.46
    # and of £148,609.45 as one value.
    (
        dict(
            employment_income=148_609.46,
            employment_expenses=108_409.45,
            savings_interest_income=9_000,
            dividend_income=1_570,
        ),
        7_440.00,
    ),
    (
        dict(
            employment_income=300_000.01,
            employment_expenses=259_800,
            savings_interest_income=9_000,
            dividend_income=1_570,
        ),
        7_440.00,
    ),
    # Pay less expenses of £50,000.01, with £500 of savings and £270 of
    # dividends at their nil rates: £37,430.01 at 20%.
    (
        dict(
            employment_income=300_000.01,
            employment_expenses=250_000,
            savings_interest_income=500,
            dividend_income=270,
        ),
        7_486.00,
    ),
    # An £800 gift raises the limit to £38,700, and £41,200.01 of pay less
    # expenses leaves £39,200.01: £38,200.01 at 20%.
    (
        dict(
            employment_income=300_000.01,
            employment_expenses=258_800,
            savings_interest_income=9_000,
            dividend_income=1_570,
            gift_aid=800,
        ),
        7_640.00,
    ),
    # Trading profits less capital allowances of £40,200.01.
    (
        dict(
            self_employment_income=224_417.13,
            capital_allowances=184_217.12,
            savings_interest_income=9_000,
            dividend_income=1_570,
        ),
        7_440.00,
    ),
    # Dividends less deficiency relief of £1,570.01, with pay of £40,200.
    (
        dict(
            employment_income=40_200,
            savings_interest_income=9_000,
            dividend_income=201_570.01,
            deficiency_relief=200_000,
        ),
        7_440.00,
    ),
    # A £9,995.19 gift grosses up to £12,493.9875 and raises the limit to
    # £50,193.9875. The Personal Allowance leaves £50,693.99, a quarter of a
    # penny over that limit plus £500: £49,693.99 at 20%. Every amount sits
    # under £65,536, and float32 sums net income to £63,263.988, 0.2p under.
    (
        dict(
            employment_income=52_693.99,
            savings_interest_income=9_000,
            dividend_income=1_570,
            gift_aid=9_995.19,
        ),
        9_938.80,
    ),
    # An £8,609.19 gift raises the limit to £48,461.4875, and the allowance
    # leaves £48,961.49, a quarter of a penny over it plus £500.
    (
        dict(
            employment_income=50_961.49,
            savings_interest_income=9_000,
            dividend_income=1_570,
            gift_aid=8_609.19,
        ),
        9_592.30,
    ),
    # A £100.03 gift raises the limit to £37,825.0375. Pay of £120,000 less
    # expenses of £79,675.02 leaves £40,324.98, and the allowance leaves
    # £38,325.04, a quarter of a penny over that limit plus £500: £37,325.04
    # at 20%. Float32 holds the pay exactly and the expenses 0.34p over, so
    # the bound comes from an amount the model takes off.
    (
        dict(
            employment_income=120_000,
            employment_expenses=79_675.02,
            savings_interest_income=9_000.06,
            dividend_income=1_570,
            gift_aid=100.03,
        ),
        7_465.01,
    ),
]

# 2026-27 recipients the model holds at the limit, for whom the amounts behind
# the income tested give no bound under a penny, so the rate test keeps room
# and the model denies the reduction, as ``main`` does. Each has £9,000 of
# savings and £1,570 of dividends and is charged £7,440.
KEEPS_ROOM_AT_THE_LIMIT = [
    # Pay of £148,609.45 less expenses of £108,409.45 is £40,200, at the limit,
    # so the law gives the reduction. Float32 holds that pay as it holds
    # £148,609.46, a penny over.
    dict(employment_income=148_609.45, employment_expenses=108_409.45),
    # Dividends of £201,570 less deficiency relief of £200,000, at the limit.
    # Both are £131,072 or more, where float32 can store two entries a penny
    # apart as one, so the entries get no bound.
    dict(employment_income=40_200, dividend_income=201_570, deficiency_relief=200_000),
]

# 2026-27 recipients entered at the limit, with amounts behind the income
# tested that float32 holds to well under a penny. The law gives each the
# reduction, and so does the model; ``main`` denies each. Each row ends with
# the law's tax.
REACHES_THE_LIMIT = [
    # Pay less expenses of £40,200: 37,700 x 20% less £252.
    (dict(employment_income=45_200, employment_expenses=5_000), 7_288.00),
    # Float32 holds £100,000.37 0.28p under and £59,800.37 0.11p over, so
    # taxable pay 0.39p under £40,200. The bound is 0.39p.
    (dict(employment_income=100_000.37, employment_expenses=59_800.37), 7_288.00),
    # Pension contributions of £5,000 under net pay.
    (
        dict(employment_income=45_200, employee_pension_contributions_reported=5_000),
        7_288.00,
    ),
    # A trading loss of £5,000 against pay of £45,200.
    (
        dict(
            employment_income=45_200, trading_loss=5_000, uses_trading_allowance=False
        ),
        7_288.00,
    ),
    # An £800 gift raises the limit to £38,700: 38,700 x 20% less £252.
    (dict(employment_income=41_200, gift_aid=800), 7_488.00),
]


def test_rate_test_reads_the_amounts_behind_the_income_it_tests():
    """Float32 can hide a penny behind amounts the rate test never reads. Pay
    of £148,609.46 less £108,409.45 of expenses leaves £40,200.01, but float32
    holds that pay as £148,609.453125 and the model holds £40,200.00. The
    amounts the test reads all sit under £65,536, so ``_low_precision`` sees
    nothing. ``_can_hide_an_excess`` bounds the float32 error from the inputs
    up, and the test keeps room wherever the bound reaches the least amount
    the entries can sit over a limit: a penny, or a quarter of a penny at a
    limit a Gift Aid gift leaves between two pence. The model then denies the
    reduction to each recipient entered over a limit, and charges the law's
    tax. It also denies it to recipients it cannot tell from those, as
    ``main`` does. It still gives the reduction at the limit where the bound
    stays under a penny."""
    year = 2026
    over = [row for row, _ in PENNY_HIDDEN_BEHIND_THE_INCOME_TESTED]
    common = dict(savings_interest_income=9_000, dividend_income=1_570)
    kept = [dict(common) | row for row in KEEPS_ROOM_AT_THE_LIMIT]
    reaches = [dict(common, **row) for row, _ in REACHES_THE_LIMIT]
    sim = explicit_couples(year, over + kept + reaches)
    reduction = sim.calculate("marriage_allowance_tax_reduction", year)[0::2]
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    denied = len(over) + len(kept)
    assert not meets[:denied].any() and not reduction[:denied].any()
    law_tax = [amount for _, amount in PENNY_HIDDEN_BEHIND_THE_INCOME_TESTED]
    assert tax[: len(over)] == pytest.approx(law_tax, abs=0.01)
    assert tax[len(over) : denied] == pytest.approx(7_440.00, abs=0.01)
    assert meets[denied:].all()
    assert reduction[denied:] == pytest.approx(252)
    assert tax[denied:] == pytest.approx(
        [amount for _, amount in REACHES_THE_LIMIT], abs=0.01
    )
    # The search and the model's answer read the same flag.
    period = periods.period(year)
    income_tax = sim.tax_benefit_system.parameters(str(year)).gov.hmrc.income_tax
    person = sim.populations["person"]
    flagged = _inputs(person, period, income_tax)["can_hide_an_excess"][0::2]
    assert flagged[:denied].all() and not flagged[denied:].any()
    assert _context(person, period, sim.tax_benefit_system.parameters).low_precision[
        0::2, 0
    ].tolist() == [True] * denied + [False] * len(reaches)


def test_held_error_follows_the_formulas_behind_the_rate_test():
    """``_held_error`` checks each amount the model holds against the float64
    sum of the amounts its formula reads (``SUMS``), so its bound stays small
    only while those sums match the formulas. The first person below enters
    every input the sums read, each in whole pence under £65,536, and the
    bound on net income and on the allowances stays under a penny. The second
    has pay of £131,072 or more, which gives no bound. The third has a company
    car, whose benefit the function does not follow, the fourth a trading loss
    over the £50,000 cap of s. 24A, and the fifth pension contributions over
    the earnings that limit their relief."""
    year = 2026
    busy = dict(
        employment_income=21_003.17,
        employment_expenses=412.39,
        statutory_sick_pay=318.44,
        self_employment_income=9_871.03,
        capital_allowances=611.27,
        loss_relief=205.11,
        private_pension_income=4_102.59,
        property_income=3_950.41,
        savings_interest_income=2_210.83,
        other_investment_income=97.21,
        dividend_income=1_733.69,
        deficiency_relief=12.07,
        trading_loss=1_044.63,
        other_deductions=310.19,
        covenanted_payments=55.43,
        charitable_investment_gifts=120.77,
        employee_pension_contributions_reported=1_250.33,
        personal_pension_contributions=480.21,
        gift_aid=163.24,
        uses_trading_allowance=False,
    )
    sim = explicit_couples(
        year,
        [
            busy,
            dict(employment_income=131_072),
            dict(employment_income=30_000, company_car_list_price=20_000),
            dict(
                employment_income=60_000,
                trading_loss=50_000.01,
                uses_trading_allowance=False,
            ),
            dict(employment_income=45_200, personal_pension_contributions=45_200.01),
        ],
    )
    period = periods.period(year)
    income_tax = sim.tax_benefit_system.parameters(str(year)).gov.hmrc.income_tax
    person = sim.populations["person"]
    known = {}
    net_income = _held_error(person, period, income_tax, "net_income", known)[0::2]
    allowances = _held_error(person, period, income_tax, "allowances", known)[0::2]
    assert sim.calculate("net_income", year)[0] == pytest.approx(41_001.90, abs=0.01)
    assert sim.calculate("allowances", year)[0] == pytest.approx(14_786.93, abs=0.01)
    assert net_income[0] < 0.01 and allowances[0] < 0.01
    # Each input's bound is its distance from whole pence.
    pay = np.float64(np.float32(21_003.17))
    assert known["employment_income"][0] == pytest.approx(abs(pay - 21_003.17))
    assert np.isinf(net_income[1:4]).all() and np.isinf(allowances[4])
    limits = marriage_allowance_rate_limits(person, period, income_tax)
    flagged = _can_hide_an_excess(person, period, income_tax, limits, np.zeros(10))
    assert flagged[0::2].tolist() == [False, True, True, True, True]


def test_rate_test_reads_an_amount_supplied_in_place_of_its_formula_as_an_entry():
    """Taxable pay of £40,200 supplied as an input, with £9,000 of savings and
    £1,570 of dividends in 2026-27, sits at the limit. The model reads the
    supplied amount in place of the formula, so it is an entry.
    ``_held_error`` bounds it by its distance from whole pence, nil here, and
    reads none of the pay, benefits and expenses the formula would. The rate
    test keeps no room, and one share meets it: £2,500 of the £12,570
    Personal Allowance against pay, £8,500 against savings and £1,570 against
    dividends. That leaves £37,700 of pay at 20%, £7,540, and £500 of savings
    at the savings nil rate: £7,288 after the £252 reduction (ITA 2007
    ss. 10, 12B, 25 and 55B). ``main`` denies the reduction and charges
    £7,440."""
    year = 2026
    sim = explicit_couples(
        year,
        [
            dict(
                taxable_employment_income=40_200,
                savings_interest_income=9_000,
                dividend_income=1_570,
            )
        ],
    )
    assert sim.calculate("meets_marriage_allowance_income_conditions", year)[0]
    reduction = sim.calculate("marriage_allowance_tax_reduction", year)[0]
    assert reduction == pytest.approx(252)
    assert sim.calculate("income_tax", year)[0] == pytest.approx(7_288.00, abs=0.01)
    period = periods.period(year)
    income_tax = sim.tax_benefit_system.parameters(str(year)).gov.hmrc.income_tax
    known = {}
    bound = _held_error(
        sim.populations["person"], period, income_tax, "net_income", known
    )
    assert bound[0] == pytest.approx(0, abs=1e-9)
    assert known["taxable_employment_income"][0] == pytest.approx(0, abs=1e-9)
    # The function stopped at the supplied amount.
    assert "employment_income" not in known


def held_errors(sim, year, name):
    """``_held_error`` for ``name``, and the bounds it worked out on the way."""
    period = periods.period(year)
    income_tax = sim.tax_benefit_system.parameters(str(year)).gov.hmrc.income_tax
    known = {}
    bound = _held_error(sim.populations["person"], period, income_tax, name, known)
    return bound, known


def can_hide_an_excess(sim, year):
    period = periods.period(year)
    income_tax = sim.tax_benefit_system.parameters(str(year)).gov.hmrc.income_tax
    return _inputs(sim.populations["person"], period, income_tax)["can_hide_an_excess"]


def test_rate_test_reads_pay_set_as_an_input_as_an_entry():
    """A married recipient with pay of £40,200, savings of £9,000 and dividends
    of £1,570 in 2026-27, whose partner has no income. The constructor moves a
    situation's pay into employment_income_before_lsr, and the model adds
    employment_income up from it. ``Simulation.set_input`` stores the pay in
    employment_income itself, as a YAML test does, with nothing behind it.
    Either way the pay is an entry in whole pence, so the rate test keeps no
    room. One share meets the test: £2,500 of the £12,570 Personal Allowance
    against pay, £8,500 against savings and £1,570 against dividends. It
    leaves £37,700 of pay at 20%, £7,540, and £500 of savings at the savings
    nil rate: £7,288 after the £252 reduction (ITA 2007 ss. 10, 12B, 25 and
    55B). ``_held_error`` reads pay set as an input as it stands, and none of
    the amounts employment_income adds up."""
    year = 2026
    others = dict(savings_interest_income=9_000, dividend_income=1_570)
    built = explicit_couples(year, [dict(employment_income=40_200, **others)])
    set_after = explicit_couples(year, [others])
    set_after.set_input("employment_income", year, [40_200, 0])
    for sim, adds_pay_up in ((built, True), (set_after, False)):
        assert sim.calculate("meets_marriage_allowance_income_conditions", year)[0]
        reduction = sim.calculate("marriage_allowance_tax_reduction", year)[0]
        assert reduction == pytest.approx(252)
        tax = sim.calculate("income_tax", year)[0]
        assert tax == pytest.approx(7_288.00, abs=0.01)
        bound, known = held_errors(sim, year, "net_income")
        assert bound[0] == pytest.approx(0, abs=1e-9)
        assert ("employment_income_before_lsr" in known) == adds_pay_up
        assert not can_hide_an_excess(sim, year).any()


def test_rate_test_keeps_room_for_pay_set_as_an_input_from_131_072():
    """Pay set through ``Simulation.set_input`` is an entry, and an entry of
    £131,072 or more gets no bound: float32 holds pay of £148,609.45 and of
    £148,609.46 both as £148,609.453125. Less £108,409.45 of expenses the
    model holds £40,200 of taxable pay for both, at the limit, with £9,000 of
    savings, £1,570 of dividends and net income of £50,770, under £65,536. The
    law gives the first recipient the reduction and denies the second, who is
    a penny over. The test keeps room for both, so the model denies both, as
    ``main`` does, and charges £500 of savings and £500 of dividends at their
    nil rates and £37,200 at 20%: £7,440 (£37,200.01 and £7,440.002 for the
    second by the law)."""
    year = 2026
    row = dict(
        employment_expenses=108_409.45,
        savings_interest_income=9_000,
        dividend_income=1_570,
    )
    sim = explicit_couples(year, [row, row])
    sim.set_input("employment_income", year, [148_609.45, 0, 148_609.46, 0])
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    reduction = sim.calculate("marriage_allowance_tax_reduction", year)[0::2]
    assert not meets.any() and not reduction.any()
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax == pytest.approx([7_440.00, 7_440.00], abs=0.01)
    # No amount the rate test reads reaches LOW_PRECISION.
    assert (sim.calculate("net_income", year) < LOW_PRECISION).all()
    bound, known = held_errors(sim, year, "net_income")
    assert np.isinf(bound[0::2]).all()
    assert np.isinf(known["employment_income"][0::2]).all()
    assert "employment_income_before_lsr" not in known
    assert can_hide_an_excess(sim, year)[0::2].all()


def test_rate_test_keeps_room_where_a_reform_replaces_a_formula(system):
    """A reform takes £10,000 off pay in working out taxable pay. Pay of
    £50,200 then leaves £40,200, at the limit, with £9,000 of savings and
    £1,570 of dividends in 2026-27. ``_held_error`` checks taxable pay against
    the pay, benefits and expenses the model's own formula reads (``SUMS``),
    which come to £50,200, so £10,000 stays unexplained and the bound is far
    over a penny. The rate test keeps room, and the model denies the reduction
    and charges £7,440: £37,200 at 20%, with £500 of savings and £500 of
    dividends at their nil rates. The reformed law gives the reduction and
    £7,288, so the £152 is the cost of the room."""
    model = type(system.variables["taxable_employment_income"])

    class taxable_employment_income(model):
        def formula(person, period, parameters):
            return np.maximum(0, person("employment_income", period) - 10_000)

    class take_10_000_off_pay(Reform):
        def apply(self):
            self.update_variable(taxable_employment_income)

    year = 2026
    sim = explicit_couples(
        year,
        [
            dict(
                employment_income=50_200,
                savings_interest_income=9_000,
                dividend_income=1_570,
            )
        ],
        reform=take_10_000_off_pay,
    )
    assert sim.calculate("taxable_employment_income", year)[0] == 40_200
    assert not sim.calculate("meets_marriage_allowance_income_conditions", year)[0]
    assert sim.calculate("marriage_allowance_tax_reduction", year)[0] == 0
    assert sim.calculate("income_tax", year)[0] == pytest.approx(7_440.00, abs=0.01)
    bound, _ = held_errors(sim, year, "net_income")
    assert bound[0] == pytest.approx(10_000)
    assert can_hide_an_excess(sim, year)[0]


def test_rate_test_bounds_the_amounts_behind_a_supplied_net_income():
    """Net income of £50,770 supplied as an input is an entry, and
    ``_held_error`` stops there. The rate test also reads savings, dividends,
    property income, the trade loss relief and pension relief on their own, so
    ``_can_hide_an_excess`` bounds each one the walk did not reach. Both
    recipients have pay of £40,200 and £9,000 of savings in 2026-27, and
    dividends of £1,570, at the limit. The first has them as £201,570 less
    £200,000 of deficiency relief. Each of those is £131,072 or more and gets
    no bound, so the test keeps room, and the model denies the reduction and
    charges £7,440, as it does without the supplied net income
    (``KEEPS_ROOM_AT_THE_LIMIT``). The second gets the reduction: £7,288. The
    law gives both the reduction and £7,288, so the first's £152 is the cost
    of the room."""
    year = 2026
    common = dict(
        net_income=50_770, employment_income=40_200, savings_interest_income=9_000
    )
    sim = explicit_couples(
        year,
        [
            dict(common, dividend_income=201_570, deficiency_relief=200_000),
            dict(common, dividend_income=1_570),
        ],
    )
    meets = sim.calculate("meets_marriage_allowance_income_conditions", year)[0::2]
    assert meets.tolist() == [False, True]
    reduction = sim.calculate("marriage_allowance_tax_reduction", year)[0::2]
    assert reduction == pytest.approx([0, 252])
    tax = sim.calculate("income_tax", year).astype(float)[0::2]
    assert tax == pytest.approx([7_440.00, 7_288.00], abs=0.01)
    bound, known = held_errors(sim, year, "net_income")
    assert bound[0::2] == pytest.approx([0, 0], abs=1e-9)
    assert "taxable_dividend_income" not in known
    assert can_hide_an_excess(sim, year)[0::2].tolist() == [True, False]


def test_rate_test_reads_a_gross_gift_supplied_as_an_input_as_an_entry():
    """A grossed-up gift of £1,000 supplied as an input raises the basic rate
    limit to £38,700 (s. 414(2)(b)), as an £800 gift does
    (``REACHES_THE_LIMIT``). With pay of £41,200, £9,000 of savings and £1,570
    of dividends in 2026-27, the Personal Allowance leaves £39,200, the limit
    plus the £500 savings allowance. The one share that meets the test leaves
    £38,700 of pay at 20%, £7,740: £7,488 after the £252 reduction. The gross
    gift is an entry in whole pence, so the rate test keeps no room, though
    no gift stands behind it."""
    year = 2026
    sim = explicit_couples(
        year,
        [
            dict(
                employment_income=41_200,
                savings_interest_income=9_000,
                dividend_income=1_570,
                gift_aid_grossed_up=1_000,
            )
        ],
    )
    assert sim.calculate("meets_marriage_allowance_income_conditions", year)[0]
    reduction = sim.calculate("marriage_allowance_tax_reduction", year)[0]
    assert reduction == pytest.approx(252)
    assert sim.calculate("income_tax", year)[0] == pytest.approx(7_488.00, abs=0.01)
    assert not can_hide_an_excess(sim, year).any()


def test_held_error_gives_a_value_the_model_stored_no_bound():
    """A scenario stores an amount it calculated with ``set_model_value``,
    which the engine keeps like an input. It is not an entry: for a trading
    allowance deduction of £500 stored that way, ``_held_error`` follows the
    variable's own rule, and a formula it does not list gets no bound. The
    same £500 set through ``Simulation.set_input`` is an entry in whole
    pence, with a nil bound."""
    year = 2026
    sim = explicit_couples(year, [dict(employment_income=40_200)])
    name = "trading_allowance_deduction"
    set_model_value(sim, name, year, np.array([500.0, 0.0]))
    bound, _ = held_errors(sim, year, name)
    assert np.isinf(bound[0]) and bound[1] == 0
    sim.set_input(name, year, np.array([500.0, 0.0]))
    bound, _ = held_errors(sim, year, name)
    assert bound.tolist() == [0, 0]

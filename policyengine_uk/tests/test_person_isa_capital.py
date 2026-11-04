"""Person cash and stocks and shares ISAs count in the holder's benefit unit (#2729).

Each means-test formula counts cash_isa_countable_capital and
stocks_and_shares_isa_countable_capital through person_sources, for the
claimant and partner. The formulas subtract them from the household source
that includes them (cash_isa and share_like_capital) and allocate the
remainder between benefit units.

For the households below, with no reported capital, the formulas allocate the
remainder by claimant weights or, for Pension Credit, pension-age adult
counts. For a UC unit that reports its capital, the formula leaves its
claimant's and partner's ISAs in the pool, and a Pension Credit report
replaces the unit's calculated capital; the YAML cases cover both. The
invariants:

1. A pound counts once. The capital the household's benefit units count,
   plus the ISAs of members no unit counts (dependants, and for Pension
   Credit holders outside a pension-age unit), equals savings, cash_isa and
   share_like_capital together, up to float32 rounding of the remainder's
   shares and each programme's penny rounding. Each programme values
   share_like_capital, and each stocks and shares ISA it moves out of it, at
   its sale-expense share (90%), and savings and cash ISAs at face value. Where balances exceed a total, the holdings sum to it exactly, so
   that source leaves nothing in the remainder: an adult with no ISA counts
   exactly the capital they count without the other members' ISAs.
2. Where the balances' stored sum exceeds the total, the holdings sum to
   the total exactly, each in proportion to its balance within the step
   invariant 7 gives; otherwise each member counts their balance exactly.
3. With no person balances, every means test gives what the lists without
   the ISA person sources give, in 2025, 2032, 2033 and 2040.
4. Differential: person balances alone and the household totals alone give
   the same capital to a one-benefit-unit household.
5. A dataset that stores a total and smaller balances counts the balances in
   their holders' units and the rest in the pool, adding up to the stored
   total #2781 keeps, in every year.
6. A reform that drops the household source drops the person source with it,
   and one that empties person_sources returns the ISAs to the pool.
7. The allocation arithmetic (bounded_holdings), for every float32 balance
   and finite total: no holding exceeds the total or falls below zero; where
   the balances' stored sum exceeds the total, the holdings' float64 sum
   equals it; where it doesn't, each holding equals the balance; a sole
   holder whose balance reaches the total holds exactly the total; each
   holding equals its proportional share rounded down or up to a whole step,
   the total's float32 spacing (at most 2**104, the largest spacing of a
   finite float32), allowing for float64 sum and division rounding, so it
   lies within one step of the share and passes a capital limit only where
   the share does; a holding exceeds its balance by less than one step, and
   only where the balance falls between steps; and the same input gives the
   same output.
"""

import math
from contextlib import contextmanager
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.populations import GroupPopulation, Population

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import PROJECTION_END_YEAR
from policyengine_uk.entities import Household, Person
from policyengine_uk.system import system
from policyengine_uk.variables.gov.dwp._person_capital_pool import (
    HOUSEHOLD_SOURCE_OF,
    bounded_holdings,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025
YEARS = (YEAR, PROJECTION_END_YEAR, PROJECTION_END_YEAR + 1, 2040)
CAPITAL = {
    "uc_assessable_capital": "gov.dwp.universal_credit.means_test.capital",
    "housing_benefit_assessable_capital": "gov.dwp.housing_benefit.means_test.capital",
    "pension_credit_assessable_capital": "gov.dwp.pension_credit.income.capital",
    "income_support_assessable_capital": "gov.dwp.income_support.means_test.capital",
    "jsa_income_assessable_capital": "gov.dwp.JSA.income.capital",
    "esa_income_assessable_capital": "gov.dwp.ESA.income.capital",
}
MEANS_TEST_CAPITAL = (*CAPITAL, "council_tax_reduction_assessable_capital")
ISA_SOURCES = tuple(HOUSEHOLD_SOURCE_OF)
BALANCE = {
    "cash_isa_countable_capital": "cash_isa_balance",
    "stocks_and_shares_isa_countable_capital": "stocks_and_shares_isa_balance",
}
# The person_sources lists before #2729: the Lifetime ISA alone.
WITHOUT_ISA_SOURCES = {
    f"{path}.person_sources": {
        "2017-04-06.2100-12-31": ["lifetime_isa_countable_capital"]
    }
    for path in CAPITAL.values()
}
SETTINGS = settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
    database=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def _node(path):
    node = system.parameters
    for part in path.split("."):
        node = getattr(node, part)
    return node


def _dataset(households, year=YEAR, claims=True):
    """A dataset with one household per entry.

    Each household is a dict with ``units``, a list of benefit units, each a
    list of people as ``(age, person columns)``, and household columns.
    Without ``claims``, no benefit unit claims Universal Credit or Income
    Support, so Housing Benefit assesses capital rather than passporting it.
    """
    people, benunits = [], []
    for h, household in enumerate(households, start=1):
        for unit in household["units"]:
            benunits.append(len(benunits) + 1)
            for age, columns in unit:
                people.append(
                    {
                        "person_id": len(people) + 1,
                        "person_benunit_id": benunits[-1],
                        "person_household_id": h,
                        "age": age,
                        **columns,
                    }
                )
    people = pd.DataFrame(people).fillna(0.0)
    columns = sorted({name for h in households for name in h if name != "units"})
    count = len(households)
    benunit = pd.DataFrame({"benunit_id": benunits})
    if not claims:
        benunit["would_claim_uc"] = False
        benunit["would_claim_IS"] = False
    return UKSingleYearDataset(
        person=people,
        benunit=benunit,
        household=pd.DataFrame(
            {
                "household_id": range(1, count + 1),
                "household_weight": [1.0] * count,
                "region": ["LONDON"] * count,
                "tenure_type": ["RENT_PRIVATELY"] * count,
                "council_tax": [1_500.0] * count,
                "rent": [12_000.0] * count,
                **{
                    name: [float(h.get(name, 0.0)) for h in households]
                    for name in columns
                },
            }
        ),
        fiscal_year=year,
    )


def _core_household(household_of):
    """Core's person population, and its household, for the given households.

    Builds Core's own populations by hand, with no Simulation, so the
    allocation properties run in milliseconds.
    """
    person = Population(Person)
    person.count = len(household_of)
    household = GroupPopulation(Household, person)
    household.members_entity_id = np.asarray(household_of, dtype=np.intp)
    household.count = int(max(household_of)) + 1
    return person, household


def _core_household_sum(household_of):
    """Core's person.household.sum, for people in the given households."""
    _, household = _core_household(household_of)
    return lambda array: household.project(household.sum(array))


def _household_rank(household_of):
    """Each member's rank in their household, lowest first, ties in member order.

    Plain numpy, for the allocation properties; Core's
    person.get_rank(person.household, ...) gives the same ranks.
    """
    household_of = np.asarray(household_of)
    index = np.arange(household_of.size)

    def rank(criteria):
        # Sort by household, then criteria, then member order, and count each
        # member's place from their household's first place.
        order = np.lexsort((index, np.asarray(criteria), household_of))
        grouped = household_of[order]
        first = np.r_[True, grouped[1:] != grouped[:-1]]
        place = np.arange(order.size)
        ranks = np.empty(order.size, dtype=int)
        ranks[order] = place - np.maximum.accumulate(np.where(first, place, 0))
        return ranks

    return rank


ANY_FLOAT32 = st.floats(width=32)
FINITE_FLOAT32 = st.floats(width=32, allow_nan=False, allow_infinity=False)
POUNDS = st.integers(min_value=0, max_value=4_000_000).map(
    lambda pence: float(np.float32(pence / 100))
)
# Up to three households of up to six people; amounts anywhere in float32 or
# in pounds and pence, where ISAs and capital limits sit.
ALLOCATIONS = st.integers(min_value=1, max_value=3).flatmap(
    lambda count: st.tuples(
        st.lists(st.one_of(POUNDS, FINITE_FLOAT32), min_size=count, max_size=count),
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=count - 1),
                st.one_of(POUNDS, ANY_FLOAT32),
            ),
            min_size=1,
            max_size=6,
        ),
    )
)
ALLOCATION_SETTINGS = settings(SETTINGS, max_examples=300)


@ALLOCATION_SETTINGS
@given(allocation=ALLOCATIONS)
# A sole holder over the total at UC's capital limit, its tariff threshold
# and Pension Credit's tariff threshold, alone and beside two others.
@example(allocation=([16_000.0], [(0, 16_790.0)]))
@example(allocation=([6_000.0], [(0, 8_341.0)]))
@example(allocation=([10_000.0], [(0, 16_450.0), (0, 0.0), (0, 0.0)]))
# A couple over the total beside an adult with no ISA, whose shares round
# down to one step short of it at the UC tariff threshold and limit.
@example(allocation=([32_000.0], [(0, 0.0), (0, 12_000.0), (0, 24_000.0)]))
@example(allocation=([64_000.0], [(0, 0.0), (0, 24_000.0), (0, 48_000.0)]))
# Three equal balances with steps left over for some of them.
@example(allocation=([10.0], [(0, 3.0), (0, 3.0), (0, 3.0)]))
# Three holders of exactly 16,000 and of 6,000 under totals one step short
# of their sum: each share falls just short of the balance, and no holding
# may pass it.
@example(allocation=([47_999.99609375], [(0, 16_000.0)] * 3))
@example(allocation=([17_999.998046875], [(0, 6_000.0)] * 3))
# Shares that round to the nearest float32 overshoot the total.
@example(
    allocation=(
        [46_000.98046875],
        [(0, 10_000.0), (0, 10_000.0), (0, 16_001.0), (0, 10_000.0)],
    )
)
# Balances whose float64 sum exceeds the total but rounds to it in float32.
@example(allocation=([16_000.0], [(0, 8_000.00048828125), (0, 8_000.0)]))
# A balance too small to change the float64 sum, beside one over the total.
@example(allocation=([1.0], [(0, 1e-30), (0, 3.0)]))
# Balances whose sum exceeds float32's range.
@example(allocation=([3e38], [(0, 3e38), (0, 3e38)]))
# A total of float32's largest value, whose next float32 is infinite.
@example(allocation=([3.4028235e38], [(0, 3.4028235e38), (0, 3.4028235e38)]))
# Shares above 2**127, where every float32 lies on a grid of 2**104.
@example(allocation=([3e38], [(0, 3e38), (0, 2e38)]))
# Infinite, missing and negative balances, and a negative total.
@example(
    allocation=(
        [5.0, -7.0],
        [(0, float("inf")), (1, float("nan")), (1, -float("inf")), (0, -3.0)],
    )
)
def test_holdings_stay_within_the_household_total(allocation):
    """Invariant 7: the arithmetic every ISA person source shares."""
    totals, members = allocation
    household_of = np.array([h for h, _ in members])
    household_sum = _core_household_sum(household_of)
    household_rank = _household_rank(household_of)
    balance = np.array([b for _, b in members], np.float32)
    total = np.array(totals, np.float32)[household_of]
    holding = bounded_holdings(balance, total, household_sum, household_rank)
    assert holding.dtype == np.float32

    cap = np.maximum(np.float32(0), total)
    held = np.where(np.isposinf(balance), cap, np.where(balance > 0, balance, 0))
    held = held.astype(np.float32)
    # The plain numpy rank agrees with Core's get_rank.
    person, household = _core_household(household_of)
    assert np.array_equal(household_rank(-held), person.get_rank(household, -held))
    # No holding falls below zero or exceeds the household total.
    assert ((0 <= holding) & (holding <= cap)).all()
    with np.errstate(over="ignore"):
        scales = household_sum(held).astype(np.float32) > cap
    # Over a total, the holdings' float64 sum equals it exactly, so each
    # means test nets the whole total from the household source and leaves
    # nothing of it in the pool.
    assert np.array_equal(household_sum(holding)[scales], cap[scales])
    # Balances whose stored sum doesn't exceed the total keep their exact values.
    assert np.array_equal(holding[~scales], held[~scales])
    # A sole holder whose balance reaches the total holds exactly the total.
    holders = household_sum((held > 0).astype(np.float32))
    sole = (held > 0) & (holders == 1) & (held >= cap)
    assert np.array_equal(holding[sole], cap[sole])
    # Over a total, each holding equals its exact proportional share rounded
    # down or up to a whole step, the total's float32 spacing, allowing for
    # float64 sum and division rounding. So it lies within one step of the
    # share and passes a multiple of the step, such as a capital limit, only
    # where the share does. A holding exceeds its balance by less than one
    # step, and only where the balance falls between steps.
    for i in np.flatnonzero(scales):
        same = np.flatnonzero(household_of == household_of[i])
        exact = (
            Fraction(float(held[i]))
            * Fraction(float(cap[i]))
            / sum(Fraction(float(held[j])) for j in same)
        )
        step = Fraction(2) ** max(math.frexp(float(cap[i]))[1] - 24, -149)
        slack = exact / 2**48
        below = math.floor((exact - slack) / step) * step
        above = math.ceil((exact + slack) / step) * step
        assert below <= Fraction(float(holding[i])) <= above
        excess = Fraction(float(holding[i])) - Fraction(float(held[i]))
        assert excess < step
        if (Fraction(float(held[i])) / step).denominator == 1:
            assert excess <= 0
    # The same input gives the same output, and one household's holdings
    # never depend on another's.
    again = bounded_holdings(
        balance.copy(), total.copy(), household_sum, household_rank
    )
    assert np.array_equal(holding, again)
    for h in np.unique(household_of):
        alone = household_of == h
        own_household = np.zeros(alone.sum(), dtype=int)
        result = bounded_holdings(
            balance[alone],
            total[alone],
            _core_household_sum(own_household),
            _household_rank(own_household),
        )
        assert np.array_equal(result, holding[alone])


@pytest.mark.parametrize("limit", [6_000, 10_000, 16_000])
def test_a_sole_holder_over_a_limit_holds_exactly_the_limit(limit):
    """Invariant 7, exhaustively near three capital limits.

    Whole-pound balances from the limit up to, but excluding, four times it,
    plus 1,000 adjacent float32 values starting at the limit, each a sole
    holder under a household total equal to the limit.
    """
    above = np.nextafter(np.float32(limit), np.float32(np.inf))
    steps = np.arange(1_000, dtype=np.float32) * (above - np.float32(limit))
    balance = np.concatenate(
        [np.arange(limit, 4 * limit, dtype=np.float32), np.float32(limit) + steps]
    )
    total = np.full_like(balance, limit)
    households = np.arange(balance.size)
    holding = bounded_holdings(
        balance, total, _core_household_sum(households), _household_rank(households)
    )
    assert (holding == np.float32(limit)).all()


# A couple and a lodger; pensioners and their adult son; a parent and child.
HOUSEHOLD_ONLY = [
    {
        "units": [[(30, {}), (28, {})], [(40, {})]],
        "savings": 3_000,
        "cash_isa": 4_000,
        "stocks_and_shares_isa": 2_000,
        "corporate_wealth": 5_000,
    },
    {
        "units": [[(70, {}), (68, {})], [(30, {})]],
        "savings": 12_000,
        "cash_isa": 6_000,
    },
    {
        "units": [[(35, {}), (8, {})]],
        "savings": 500,
        "cash_isa": 1_000,
    },
]


def test_household_only_data_keep_todays_capital():
    """Invariant 3: no balances leave the household totals in the pool."""
    data = _dataset(HOUSEHOLD_ONLY)
    simulation = Simulation(dataset=data)
    before = Simulation(dataset=data, reform=WITHOUT_ISA_SOURCES)
    for year in YEARS:
        for name in ISA_SOURCES:
            assert not simulation.calculate(name, year).any(), (name, year)
        for name in MEANS_TEST_CAPITAL:
            assert np.array_equal(
                simulation.calculate(name, year), before.calculate(name, year)
            ), (name, year)
    # The first household's pool: savings 3,000, cash_isa 4,000 and
    # corporate_wealth 5,000 (which holds the 2,000 ISA) less 10%, 4,500,
    # shared by three claimants, two of them the couple. UC rounds each to
    # the nearest penny.
    uc = simulation.calculate("uc_assessable_capital", YEAR)
    assert list(uc[:2]) == pytest.approx([7_666.67, 3_833.33], abs=0.001)


def test_both_forms_in_one_dataset_add_up_to_the_stored_total():
    """Invariant 5: a stored total above the balances keeps the rest pooled."""
    households = [
        {
            "units": [
                [(30, {"cash_isa_balance": 0.0}), (28, {})],
                [(40, {"cash_isa_balance": 10_000.0})],
            ],
            "savings": 4_000,
            "cash_isa": 15_000,
        },
        # The dataset's cash_isa column stores 0 here, and #2781 keeps a
        # stored zero over the same year's balance, so the balance counts for
        # nothing.
        {
            "units": [[(35, {"cash_isa_balance": 2_000.0})], [(45, {})]],
            "savings": 1_000,
        },
    ]
    simulation = Simulation(dataset=_dataset(households, claims=False))
    benunit_household = np.array([0, 0, 1, 1])
    for year in YEARS:
        balances = simulation.calculate("cash_isa_balance", year)
        counted = simulation.calculate("cash_isa_countable_capital", year)
        assert counted == pytest.approx(balances * [1, 1, 1, 0, 0], rel=1e-6)
        holdings = simulation.calculate("cash_isa", year) + simulation.calculate(
            "savings", year
        )
        uc = simulation.calculate("uc_assessable_capital", year)
        hb = simulation.calculate("housing_benefit_assessable_capital", year)
        for capital in (uc, hb):
            by_household = np.bincount(benunit_household, weights=capital)
            assert by_household == pytest.approx(holdings, rel=1e-6), year
        # The lodger counts their own balance on top of a third of the pool.
        pool = holdings[0] - counted[2]
        assert uc[1] == pytest.approx(pool / 3 + counted[2], rel=1e-6), year
        assert uc[0] == pytest.approx(2 * pool / 3, rel=1e-6), year
    # #2781 keeps the stored 15,000, so the formula allocates savings of 4,000
    # and the unexplained 5,000 as 6,000 and 3,000. The second household's
    # pool holds only its savings.
    assert list(simulation.calculate("cash_isa", YEAR)) == [15_000, 0]
    assert list(simulation.calculate("uc_assessable_capital", YEAR)) == [
        6_000,
        13_000,
        500,
        500,
    ]


# The shape Microcosm's producer writes (microcosm main b979d46b): adults'
# cash and stocks and shares ISA balances, and a household corporate_wealth
# that sums directly_held_shares, unit_and_investment_trusts and the stocks
# and shares ISAs, with no household cash_isa or stocks_and_shares_isa.
PRODUCER_SHAPE = [
    {
        "units": [
            [
                (30, {"cash_isa_balance": 3_000.0}),
                (28, {"stocks_and_shares_isa_balance": 2_000.0}),
            ],
            [
                (
                    40,
                    {
                        "cash_isa_balance": 5_000.0,
                        "stocks_and_shares_isa_balance": 1_000.0,
                    },
                )
            ],
        ],
        "savings": 7_000,
        "directly_held_shares": 1_500,
        "unit_and_investment_trusts": 500,
        "corporate_wealth": 5_000,
    },
    {
        "units": [
            [(70, {"cash_isa_balance": 4_000.0}), (68, {})],
            [(30, {"stocks_and_shares_isa_balance": 6_000.0})],
        ],
        "savings": 12_000,
        "unit_and_investment_trusts": 3_000,
        "corporate_wealth": 9_000,
    },
]


def _household_capital(simulation, year, share=1):
    return (
        simulation.calculate("savings", year)
        + simulation.calculate("cash_isa", year)
        + share * simulation.calculate("share_like_capital", year)
    )


def test_person_balances_without_household_totals_count_with_their_holders():
    """Core sums the balances into each total, so every balance counts."""
    simulation = Simulation(dataset=_dataset(PRODUCER_SHAPE, claims=False))
    person_household = np.array([0, 0, 0, 1, 1, 1])
    benunit_household = np.array([0, 0, 1, 1])
    for year in (YEAR, PROJECTION_END_YEAR + 1):
        for name, balance_name in BALANCE.items():
            balance = simulation.calculate(balance_name, year)
            assert np.array_equal(simulation.calculate(name, year), balance)
        for total, balance_name in (
            ("cash_isa", "cash_isa_balance"),
            ("stocks_and_shares_isa", "stocks_and_shares_isa_balance"),
        ):
            sums = np.bincount(
                person_household, weights=simulation.calculate(balance_name, year)
            )
            assert simulation.calculate(total, year) == pytest.approx(sums, rel=1e-6)
        # The itemised shares add up to corporate_wealth, which stays the pool.
        assert np.array_equal(
            simulation.calculate("share_like_capital", year),
            simulation.calculate("corporate_wealth", year),
        )
        holdings = _household_capital(
            simulation, year, _share_counted("uc_assessable_capital")
        )
        uc = simulation.calculate("uc_assessable_capital", year)
        assert np.bincount(benunit_household, weights=uc) == pytest.approx(
            holdings, rel=1e-6
        )
    # Savings 7,000 and 2,000 of non-ISA shares less 10%, 1,800, make the
    # first pool, 2,933.33 for each claimant. The couple adds a 3,000 cash ISA
    # and a 2,000 stocks and shares ISA less 10% (1,800), and the other unit a
    # 5,000 cash ISA and a 1,000 one less 10% (900). The second pool, savings
    # 12,000 and 3,000 of trusts less 10% (2,700), gives the parents 9,800
    # and their son 4,900 in UC, to which they add 4,000 and 5,400 of ISAs;
    # the pension-age parents count all 14,700 and their 4,000 in Pension
    # Credit. UC rounds to the nearest penny, and the legacy programmes
    # round down.
    expected_uc = [10_666.67, 8_833.33, 13_800, 10_300]
    assert list(simulation.calculate("uc_assessable_capital", YEAR)) == pytest.approx(
        expected_uc, abs=0.001
    )
    for name in CAPITAL:
        if name != "pension_credit_assessable_capital":
            capital = simulation.calculate(name, YEAR)
            assert list(capital[:2]) == pytest.approx(expected_uc[:2], abs=0.011), name
    assert list(
        simulation.calculate("pension_credit_assessable_capital", YEAR)
    ) == pytest.approx([0, 0, 18_700, 0], abs=0.001)


# One benefit unit each, with a child: the adults' cash and stocks and shares
# ISA balances, other shares and savings.
ONE_UNIT_CASES = [
    # Nothing at all.
    ([(0.0, 0.0)], 0.0, 0.0),
    # A cash ISA alone, beside savings.
    ([(5_000.0, 0.0)], 0.0, 2_000.0),
    # A stocks and shares ISA alone, beside other shares.
    ([(0.0, 7_000.0)], 1_500.0, 0.0),
    # A couple's ISAs of both kinds, beside savings and other shares.
    ([(3_000.0, 2_000.0), (4_000.25, 1_000.75)], 2_500.0, 6_000.0),
    # A couple's balances whose float64 sum, 16,000.00048828125, Core stores
    # as a 16,000 total, in both kinds.
    ([(8_000.00048828125, 8_000.00048828125), (8_000.0, 8_000.0)], 0.0, 0.0),
]


def test_balances_alone_and_totals_alone_give_one_unit_the_same_capital():
    """Invariant 4, differential: the two forms of the same holdings."""
    balances, totals = [], []
    for adults, other_shares, savings in ONE_UNIT_CASES:
        shares = sum(amounts[1] for amounts in adults)
        common = {"savings": savings, "corporate_wealth": other_shares + shares}
        people = [
            (40 + i, {"cash_isa_balance": c, "stocks_and_shares_isa_balance": s})
            for i, (c, s) in enumerate(adults)
        ]
        balances.append({"units": [people + [(8, {})]], **common})
        totals.append(
            {
                "units": [[(40 + i, {}) for i in range(len(adults))] + [(8, {})]],
                "cash_isa": sum(amounts[0] for amounts in adults),
                "stocks_and_shares_isa": shares,
                **common,
            }
        )
    balances_only = Simulation(dataset=_dataset(balances))
    totals_only = Simulation(dataset=_dataset(totals))
    for year in (YEAR, PROJECTION_END_YEAR + 1):
        for name in MEANS_TEST_CAPITAL:
            # Float32 sums in either order round alike to within a penny.
            assert balances_only.calculate(name, year) == pytest.approx(
                totals_only.calculate(name, year), rel=1e-6, abs=0.01
            ), (name, year)
    # The couple at the rounding boundary keep their exact balances.
    assert list(balances_only.calculate("cash_isa_countable_capital", YEAR)[-3:]) == [
        8_000.00048828125,
        8_000.0,
        0.0,
    ]


money = st.integers(min_value=0, max_value=2_000_000).map(lambda pence: pence / 100)
SITUATION_SETTINGS = settings(SETTINGS, max_examples=4)


def _situation(units, assets, claim_uc=False):
    """One household of the given benefit units of ``(age, cash, shares)``."""
    people, benunits = {}, {}
    for u, unit in enumerate(units):
        members = []
        for i, (age, cash, shares) in enumerate(unit):
            name = f"p{u}_{i}"
            members.append(name)
            people[name] = {
                "age": {YEAR: age},
                "cash_isa_balance": {YEAR: cash},
                "stocks_and_shares_isa_balance": {YEAR: shares},
            }
        benunits[f"b{u}"] = {
            "members": members,
            "would_claim_uc": {YEAR: claim_uc},
            "would_claim_IS": {YEAR: False},
        }
    household = {"members": list(people)}
    household |= {name: {YEAR: value} for name, value in assets.items()}
    return {"people": people, "benunits": benunits, "households": {"h": household}}


def _unit(adult_ages):
    """A benefit unit of one or two adults and up to two children."""
    adults = st.lists(st.sampled_from(adult_ages), min_size=1, max_size=2)
    children = st.lists(st.just(10), min_size=0, max_size=2)
    return st.tuples(adults, children).flatmap(
        lambda ages: st.tuples(
            *[st.tuples(st.just(age), money, money) for age in ages[0] + ages[1]]
        )
    )


HOLDINGS = st.fixed_dictionaries(
    {
        "savings": money,
        "other_shares": money,
        "cash_extra": money,
        "shares_extra": money,
        "stored": st.sampled_from(["none", "above", "below"]),
    }
)


def _assets(units, holdings):
    """Household inputs: stored totals above the balances, below them, or none."""
    people = [person for unit in units for person in unit]
    cash = sum(person[1] for person in people)
    shares = sum(person[2] for person in people)
    assets = {"savings": holdings["savings"]}
    assets["corporate_wealth"] = holdings["other_shares"] + shares
    if holdings["stored"] == "above":
        assets["cash_isa"] = cash + holdings["cash_extra"]
        assets["stocks_and_shares_isa"] = shares + holdings["shares_extra"]
        assets["corporate_wealth"] += holdings["shares_extra"]
    elif holdings["stored"] == "below":
        assets["cash_isa"] = cash / 2
        assets["stocks_and_shares_isa"] = shares / 2
    return assets


def _by_household(simulation, entity, array):
    """Sum a person or benefit unit array over each household, in float64."""
    person_household = simulation.populations["household"].members_entity_id
    if entity == "person":
        index = person_household
    else:
        index = np.zeros(simulation.populations["benunit"].count, dtype=int)
        index[simulation.populations["benunit"].members_entity_id] = person_household
    return np.bincount(
        index,
        weights=np.asarray(array, np.float64),
        minlength=simulation.populations["household"].count,
    )


def _check_counted_isas(simulation):
    """Invariant 2, in each household of the simulation.

    Where the balances' stored sum exceeds the total, the holdings sum to it
    exactly, each within one step of the total of its proportional share;
    otherwise each member counts their balance exactly.
    """
    totals = {
        "cash_isa_countable_capital": simulation.calculate("cash_isa", YEAR),
        "stocks_and_shares_isa_countable_capital": np.minimum(
            simulation.calculate("stocks_and_shares_isa", YEAR),
            simulation.calculate("share_like_capital", YEAR),
        ),
    }
    person_household = simulation.populations["household"].members_entity_id
    counted = {}
    for name, total in totals.items():
        balance = simulation.calculate(BALANCE[name], YEAR)
        counted[name] = simulation.calculate(name, YEAR)
        total = np.maximum(np.float32(0), total)
        scales = _by_household(simulation, "person", balance).astype(np.float32) > total
        assert np.array_equal(
            _by_household(simulation, "person", counted[name])[scales],
            total[scales].astype(np.float64),
        ), name
        member_scales = scales[person_household]
        step = np.spacing(total)[person_household]
        sums = _by_household(simulation, "person", balance)[person_household]
        share = (
            balance
            * total[person_household].astype(np.float64)
            / np.where(member_scales, sums, 1)
        )
        assert (counted[name] >= 0).all(), name
        assert (abs(counted[name] - share) <= step)[member_scales].all(), name
        assert (counted[name] <= balance + step).all(), name
        assert np.array_equal(counted[name][~member_scales], balance[~member_scales]), (
            name
        )
    return counted


def _share_counted(variable):
    """The share of share_like_capital's market value ``variable`` counts.

    The programme counts share_like_capital, and each stocks and shares ISA
    balance it moves out of it, less its sale-expense rate where its
    ``sale_expenses.sources`` lists share_like_capital.
    """
    capital = _node(CAPITAL[variable])
    date = f"{YEAR}-01-01"
    if "share_like_capital" in capital.sale_expenses.sources(date):
        return 1 - capital.sale_expenses.rate(date)
    return 1


# The share of each ISA person source's value a programme counts, given the
# share it counts of share_like_capital.
def _isa_shares(share):
    return {
        "cash_isa_countable_capital": 1,
        "stocks_and_shares_isa_countable_capital": share,
    }


def _holdings(simulation, share=1):
    return (
        simulation.calculate("savings", YEAR)
        + simulation.calculate("cash_isa", YEAR)
        + share * simulation.calculate("share_like_capital", YEAR)
    )


@SITUATION_SETTINGS
@given(
    units=st.lists(_unit([30, 38]), min_size=1, max_size=3),
    holdings=HOLDINGS,
)
def test_a_pound_counts_once_in_working_age_means_tests(units, holdings):
    """Invariant 1 for UC, HB, IS, JSA and ESA, nobody on a claim path."""
    assets = _assets(units, holdings)
    simulation = Simulation(situation=_situation(units, assets))
    counted = _check_counted_isas(simulation)
    dependants = ~simulation.calculate("is_claimant_or_partner", YEAR)
    for name in (
        "uc_assessable_capital",
        "housing_benefit_assessable_capital",
        "income_support_assessable_capital",
        "jsa_income_assessable_capital",
        "esa_income_assessable_capital",
    ):
        share = _share_counted(name)
        weights = _isa_shares(share)
        uncounted = sum(
            (weights[source] * amount * dependants).sum()
            for source, amount in counted.items()
        )
        capital = simulation.calculate(name, YEAR)
        # Float32 shares of the remainder, and each valuation's penny
        # rounding, come to within a few pence.
        assert capital.sum() + uncounted == pytest.approx(
            _holdings(simulation, share)[0], rel=1e-5, abs=0.05
        ), name
        # Each unit counts at least its own claimant's and partner's ISAs.
        own = sum(
            simulation.map_result(
                weights[source] * amount * ~dependants, "person", "benunit", how="sum"
            )
            for source, amount in counted.items()
        )
        assert (capital >= own * (1 - 1e-6) - 0.01).all(), name


# Households for Pension Credit's pool: each a list of benefit units of
# (age, person columns), with household columns. _dataset gives every
# household each column any household has, and #2781 keeps a stored zero
# over the balances, so households with no stored totals take a dataset of
# their own.
NO_STORED_TOTALS = [
    # A pensioner couple, both with ISAs, and an unrelated working-age holder.
    {
        "units": [
            [
                (
                    70,
                    {
                        "cash_isa_balance": 3_000.0,
                        "stocks_and_shares_isa_balance": 1_000.0,
                    },
                ),
                (68, {"cash_isa_balance": 2_000.0}),
            ],
            [
                (
                    30,
                    {
                        "cash_isa_balance": 4_000.0,
                        "stocks_and_shares_isa_balance": 500.0,
                    },
                )
            ],
        ],
        "savings": 5_000,
        "corporate_wealth": 2_500 + 1_500,
    },
]
STORED_TOTALS = [
    # Totals above the balances: a pensioner with a child who holds a junior
    # ISA, and a separate pension-age unit.
    {
        "units": [
            [
                (
                    75,
                    {
                        "cash_isa_balance": 1_000.0,
                        "stocks_and_shares_isa_balance": 2_000.0,
                    },
                ),
                (10, {"cash_isa_balance": 700.0}),
            ],
            [(72, {"stocks_and_shares_isa_balance": 3_000.0})],
        ],
        "savings": 4_000,
        "cash_isa": 1_700 + 2_500,
        "stocks_and_shares_isa": 5_000 + 1_500,
        "corporate_wealth": 2_000 + 5_000 + 1_500,
    },
    # Totals below the balances, so the formulas scale them: two separate
    # pension-age units and an unrelated working-age holder.
    {
        "units": [
            [
                (
                    70,
                    {
                        "cash_isa_balance": 6_000.0,
                        "stocks_and_shares_isa_balance": 4_000.0,
                    },
                )
            ],
            [(71, {"cash_isa_balance": 3_000.0})],
            [
                (
                    30,
                    {
                        "cash_isa_balance": 2_000.0,
                        "stocks_and_shares_isa_balance": 2_000.0,
                    },
                )
            ],
        ],
        "savings": 1_000,
        "cash_isa": 11_000 / 3,
        "stocks_and_shares_isa": 2_000,
        "corporate_wealth": 6_000 + 500,
    },
]


@pytest.mark.parametrize("households", [NO_STORED_TOTALS, STORED_TOTALS])
def test_a_pound_counts_once_in_pension_credit(households):
    """Invariant 1 for Pension Credit, shared by pension-age adults only."""
    simulation = Simulation(dataset=_dataset(households, claims=False))
    counted = _check_counted_isas(simulation)
    pension_age = simulation.calculate(
        "has_attained_state_pension_credit_qualifying_age", YEAR
    )
    in_pension_unit = (
        simulation.map_result(
            simulation.map_result(pension_age, "person", "benunit", how="sum") > 0,
            "benunit",
            "person",
        )
        > 0
    )
    counts = simulation.calculate("is_claimant_or_partner", YEAR) & in_pension_unit
    share = _share_counted("pension_credit_assessable_capital")
    weights = _isa_shares(share)
    uncounted = sum(
        _by_household(simulation, "person", weights[source] * amount * ~counts)
        for source, amount in counted.items()
    )
    capital = simulation.calculate("pension_credit_assessable_capital", YEAR)
    # Float32 shares of the remainder, and each valuation's penny rounding,
    # come to within a few pence.
    assert _by_household(simulation, "benunit", capital) + uncounted == pytest.approx(
        _holdings(simulation, share), rel=1e-5, abs=0.05
    )
    if households is STORED_TOTALS:
        # The last household's ISA holdings sum exactly to its totals, so its
        # pool keeps savings of 1,000 and the 4,500 of share_like_capital
        # beyond its 2,000 of ISAs, which Pension Credit values less 10% at
        # 4,050: 2,525 for each pension-age adult.
        own = sum(weights[source] * amount for source, amount in counted.items())
        assert list(capital[-3:]) == pytest.approx(
            [2_525 + own[-3], 2_525 + own[-2], 0], rel=1e-6, abs=0.01
        )


# An adult with no ISA beside a couple whose cash ISAs exceed the household's
# cash_isa: (adults' age, cash_isa, the couple's balances, savings). The
# savings leave the adult exactly at a threshold: UC's tariff threshold of
# 6,000 and capital limit of 16,000, and Pension Credit's deemed income
# threshold of 10,000.
THRESHOLDS = {
    "uc_tariff": (30, 32_000, (12_000, 24_000), 18_000),
    "uc_limit": (30, 64_000, (24_000, 48_000), 48_000),
    "pension_credit_deemed_income": (70, 32_000, (12_000, 24_000), 30_000),
}
THRESHOLD_OUTPUTS = (
    "uc_assessable_capital",
    "uc_tariff_income",
    "is_uc_eligible",
    "pension_credit_assessable_capital",
    "pension_credit_deemed_income",
    "is_pension_credit_eligible",
)
NO_CLAIMS = {
    name: {YEAR: False}
    for name in (
        "would_claim_uc",
        "would_claim_IS",
        "would_claim_pc",
        "housing_benefit_on_passporting_benefit",
    )
}


def _threshold_situation():
    """Each threshold household, then the same without the couple's ISAs.

    A last household holds three single adults, each with a 16,000 cash ISA,
    under a cash_isa one float32 step short of their 48,000.
    """
    people, benunits, households = {}, {}, {}
    for case, (age, total, balances, savings) in THRESHOLDS.items():
        for form, keeps_isas in (("isas", True), ("reference", False)):
            home = f"{case}_{form}"
            names = [f"{home}_adult", f"{home}_holder_a", f"{home}_holder_b"]
            for name, balance in zip(names, (0, *balances)):
                people[name] = {
                    "age": {YEAR: age},
                    "cash_isa_balance": {YEAR: balance if keeps_isas else 0},
                }
            benunits[f"{home}_adult"] = {"members": names[:1], **NO_CLAIMS}
            benunits[f"{home}_couple"] = {"members": names[1:], **NO_CLAIMS}
            households[home] = {
                "members": names,
                "savings": {YEAR: savings},
                "cash_isa": {YEAR: total if keeps_isas else 0},
            }
    names = [f"holder_{i}" for i in range(3)]
    for name in names:
        people[name] = {"age": {YEAR: 30}, "cash_isa_balance": {YEAR: 16_000}}
        benunits[name] = {"members": [name], **NO_CLAIMS}
    households["holders"] = {
        "members": names,
        "cash_isa": {YEAR: float(np.nextafter(np.float32(48_000), np.float32(0)))},
    }
    return {"people": people, "benunits": benunits, "households": households}


def test_isas_over_a_total_leave_an_unrelated_adult_exactly_at_a_threshold():
    """Invariant 1, exactly, at three thresholds.

    Rounding each scaled holding down would leave a remainder that the pool
    shares with the adult: UC capital of 6,000.00048828125 and annual tariff
    income of 52.20 rather than 0. The holdings sum exactly to cash_isa, so
    the adult counts exactly what they count without the couple's ISAs.
    """
    simulation = Simulation(situation=_threshold_situation())
    outputs = {name: simulation.calculate(name, YEAR) for name in THRESHOLD_OUTPUTS}
    cash = simulation.calculate("cash_isa_countable_capital", YEAR)
    # Each case takes four units (adult and couple, with ISAs and without)
    # and six people.
    differences = {
        (case, name): (values[4 * c], values[4 * c + 2])
        for c, case in enumerate(THRESHOLDS)
        for name, values in outputs.items()
        if values[4 * c] != values[4 * c + 2]
    }
    assert not differences
    for c, (case, (age, total, balances, savings)) in enumerate(THRESHOLDS.items()):
        capital = (
            "pension_credit_assessable_capital"
            if age >= 66
            else "uc_assessable_capital"
        )
        assert outputs[capital][4 * c] == savings / 3, case
        couple = cash[6 * c + 1 : 6 * c + 3]
        assert couple.sum(dtype=np.float64) == total, case
    assert outputs["uc_tariff_income"][0] == 0
    assert outputs["is_uc_eligible"][4]
    assert outputs["pension_credit_deemed_income"][8] == 0
    # The three holders' shares come to 15,999.9987 each. Each holding equals
    # that share rounded down or up to a step of 1/256, so none passes the
    # 16,000 limit its share stays under, and the three sum to cash_isa.
    holders = cash[-3:]
    assert list(holders) == [16_000, 16_000, 16_000 - 2**-8]
    assert holders.sum(dtype=np.float64) == np.nextafter(
        np.float32(48_000), np.float32(0)
    )
    assert outputs["is_uc_eligible"][-3:].all()


LODGER = {
    "people": {
        "tenant": {"age": {YEAR: 30}},
        "lodger": {
            "age": {YEAR: 30},
            "cash_isa_balance": {YEAR: 10_000},
            "stocks_and_shares_isa_balance": {YEAR: 4_000},
        },
    },
    "benunits": {
        "tenant_unit": {"members": ["tenant"], "would_claim_uc": {YEAR: False}},
        "lodger_unit": {"members": ["lodger"], "would_claim_uc": {YEAR: False}},
    },
    "households": {
        "household": {"members": ["tenant", "lodger"], "savings": {YEAR: 2_000}}
    },
}


@contextmanager
def _law(simulation, path, value):
    """Change one parameter in place for YEAR, then restore it."""
    parameters = simulation.tax_benefit_system.parameters
    original = list(parameters.get_child(path)(f"{YEAR}-01-01"))

    def update(new):
        parameters.get_child(path).update(period=str(YEAR), value=new)
        simulation.tax_benefit_system.reset_parameter_caches()
        simulation.reset_calculations()

    update(value)
    try:
        yield
    finally:
        update(original)


def test_reforms_to_either_list_keep_each_isa_with_its_household_source():
    """Invariant 6, on one simulation whose law changes in place."""
    simulation = Simulation(situation=LODGER)
    uc_path = CAPITAL["uc_assessable_capital"]

    def capital(name):
        return list(simulation.calculate(name, YEAR))

    # The lodger's unit counts the 10,000 cash ISA and the 4,000 stocks and
    # shares ISA less 10% (3,600), and half the 2,000 of savings.
    assert capital("uc_assessable_capital") == [1_000, 14_600]
    assert capital("housing_benefit_assessable_capital") == [1_000, 14_600]
    sources = list(_node(uc_path + ".sources")(f"{YEAR}-01-01"))
    # Dropping cash_isa from UC's sources: savings 2,000 shared, and the
    # lodger keeps their stocks and shares ISA less 10%. Dropping
    # share_like_capital: the 10,000 cash ISA stays theirs.
    for dropped, expected in (
        ("cash_isa", [1_000, 4_600]),
        ("share_like_capital", [1_000, 11_000]),
    ):
        kept = [name for name in sources if name != dropped]
        with _law(simulation, uc_path + ".sources", kept):
            assert capital("uc_assessable_capital") == expected, dropped
    # Emptying UC's person_sources returns both ISAs to the pool: savings
    # 2,000, the cash ISA and the stocks and shares ISA less 10%, 15,600 in
    # all, shared by two claimants. Housing Benefit keeps its own lists.
    with _law(simulation, uc_path + ".person_sources", []):
        assert capital("uc_assessable_capital") == [7_800, 7_800]
        assert capital("housing_benefit_assessable_capital") == [1_000, 14_600]
    assert capital("uc_assessable_capital") == [1_000, 14_600]


@pytest.mark.parametrize("variable", CAPITAL)
@pytest.mark.parametrize("date", ["2016-04-05", "2025-01-01", "2040-01-01"])
def test_lists_count_each_isa_once(variable, date):
    """Each person ISA source sits beside the household source that holds it."""
    node = _node(CAPITAL[variable])
    person_sources = list(node.person_sources(date))
    sources = list(node.sources(date))
    assert [name for name in person_sources if name in ISA_SOURCES] == list(ISA_SOURCES)
    assert ("lifetime_isa_countable_capital" in person_sources) == (
        date >= "2017-04-06"
    )
    for name in ISA_SOURCES:
        assert HOUSEHOLD_SOURCE_OF[name] in sources
        assert name in system.variables
    # The household pool never names the balances or the ISA total itself.
    assert not {*BALANCE.values(), "stocks_and_shares_isa"} & set(sources)


def test_jsa_counts_isas_from_when_they_existed():
    """ISAs exist from 6 April 1999 (SI 1998/1870 reg 1)."""
    node = _node(CAPITAL["jsa_income_assessable_capital"])
    assert list(node.person_sources("1999-04-05")) == []
    assert list(node.person_sources("1999-04-06")) == list(ISA_SOURCES)

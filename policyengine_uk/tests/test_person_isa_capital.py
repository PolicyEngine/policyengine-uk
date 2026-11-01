"""Person cash and stocks and shares ISAs count in the holder's benefit unit (#2729).

Each means test counts cash_isa_countable_capital and
stocks_and_shares_isa_countable_capital through person_sources, for the
claimant and partner, and takes them out of the household pool (cash_isa and
share_like_capital) before sharing the rest between benefit units.

Invariants, for any nonnegative amounts:

1. A pound counts once. Where the pool is shared by claimant weights (or, for
   Pension Credit, pension-age adults), the capital the household's benefit
   units count, plus the ISAs of members no unit counts (dependants, and for
   Pension Credit holders outside a pension-age unit), equals savings,
   cash_isa and share_like_capital together.
2. The household counts min(sum of balances, total) of each ISA kind, each
   member at most their balance, and members over a total in proportion to
   their balances.
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
   and finite total: no holding exceeds the total; the household's stored sum
   of holdings never exceeds it, so every remainder stays at or above zero; a
   sole holder whose balance reaches the total holds exactly the total;
   balances whose stored sum is within the total keep their exact values;
   holdings over a total lie within float32 spacing of their proportional
   shares; and the same input gives the same output.
"""

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


def _core_household_sum(household_of):
    """Core's person.household.sum, for people in the given households.

    Builds Core's own populations by hand, with no Simulation, so the
    allocation properties run in milliseconds.
    """
    person = Population(Person)
    person.count = len(household_of)
    household = GroupPopulation(Household, person)
    household.members_entity_id = np.asarray(household_of, dtype=np.intp)
    household.count = int(max(household_of)) + 1
    return lambda array: household.project(household.sum(array))


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
# Balances whose float64 sum exceeds the total but rounds to it in float32.
@example(allocation=([16_000.0], [(0, 8_000.00048828125), (0, 8_000.0)]))
# A balance too small to change the float64 sum, beside one over the total.
@example(allocation=([1.0], [(0, 1e-30), (0, 3.0)]))
# Balances whose sum exceeds float32's range.
@example(allocation=([3e38], [(0, 3e38), (0, 3e38)]))
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
    balance = np.array([b for _, b in members], np.float32)
    total = np.array(totals, np.float32)[household_of]
    holding = bounded_holdings(balance, total, household_sum)
    assert holding.dtype == np.float32

    cap = np.maximum(np.float32(0), total)
    held = np.where(np.isposinf(balance), cap, np.where(balance > 0, balance, 0))
    held = held.astype(np.float32)
    # No holding is negative or exceeds the household total.
    assert ((0 <= holding) & (holding <= cap)).all()
    # Core stores the household's sum of holdings, as each means test nets it
    # from the household source, within the total.
    with np.errstate(over="ignore"):
        stored = household_sum(holding).astype(np.float32)
        within = household_sum(held).astype(np.float32) <= cap
    assert (cap - stored >= 0).all()
    # Balances whose stored sum is within the total keep their exact values.
    assert np.array_equal(holding[within], held[within])
    # A sole holder whose balance reaches the total holds exactly the total.
    holders = household_sum((held > 0).astype(np.float32))
    sole = (held > 0) & (holders == 1) & (held >= cap)
    assert np.array_equal(holding[sole], cap[sole])
    # Over a total, each holding lies within float32 spacing (plus float64
    # rounding) of its exact proportional share, and together they fall
    # short of the total by at most one float32 spacing per member.
    for i in np.flatnonzero(~within):
        same = np.flatnonzero(household_of == household_of[i])
        exact = (
            Fraction(float(held[i]))
            * Fraction(float(cap[i]))
            / sum(Fraction(float(held[j])) for j in same)
        )
        spacing = Fraction(float(np.spacing(np.float32(float(exact)))))
        assert abs(Fraction(float(holding[i])) - exact) <= spacing + exact / 2**48
        assert cap[i] - stored[i] <= (len(same) + 1) * np.spacing(cap[i])
    # The same input gives the same output, and one household's holdings
    # never depend on another's.
    again = bounded_holdings(balance.copy(), total.copy(), household_sum)
    assert np.array_equal(holding, again)
    for h in np.unique(household_of):
        alone = household_of == h
        result = bounded_holdings(
            balance[alone],
            total[alone],
            _core_household_sum(np.zeros(alone.sum(), dtype=int)),
        )
        assert np.array_equal(result, holding[alone])


@pytest.mark.parametrize("limit", [6_000, 10_000, 16_000])
def test_a_sole_holder_over_a_limit_holds_exactly_the_limit(limit):
    """Invariant 7, exhaustively near three capital limits.

    Every float32 balance from the limit to four times it, each a sole
    holder under a household total equal to the limit, and the next 1,000
    float32 balances above the limit.
    """
    above = np.nextafter(np.float32(limit), np.float32(np.inf))
    steps = np.arange(1_000, dtype=np.float32) * (above - np.float32(limit))
    balance = np.concatenate(
        [np.arange(limit, 4 * limit, dtype=np.float32), np.float32(limit) + steps]
    )
    total = np.full_like(balance, limit)
    household_sum = _core_household_sum(np.arange(balance.size))
    holding = bounded_holdings(balance, total, household_sum)
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
    # corporate_wealth 5,000 (which holds the 2,000 ISA), shared by three
    # claimants, two of them the couple.
    uc = simulation.calculate("uc_assessable_capital", YEAR)
    assert list(uc[:2]) == [8_000, 4_000]


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
    # #2781 keeps the stored 15,000: savings 4,000 and its unexplained 5,000
    # make a pool of 9,000, shared 6,000 and 3,000. The second household's
    # savings are its whole pool.
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


def _household_capital(simulation, year):
    return sum(
        simulation.calculate(name, year)
        for name in ("savings", "cash_isa", "share_like_capital")
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
        holdings = _household_capital(simulation, year)
        uc = simulation.calculate("uc_assessable_capital", year)
        assert np.bincount(benunit_household, weights=uc) == pytest.approx(
            holdings, rel=1e-6
        )
    # Savings 7,000 and 2,000 of non-ISA shares make the first pool, 3,000 for
    # each claimant, and each unit adds its members' 5,000 and 6,000 of ISAs.
    # The second pool, savings 12,000 and 3,000 of trusts, gives the parents
    # 10,000 and their son 5,000 in UC, and the pension-age parents all
    # 15,000 in Pension Credit.
    expected_uc = [11_000, 9_000, 14_000, 11_000]
    assert list(simulation.calculate("uc_assessable_capital", YEAR)) == expected_uc
    for name in CAPITAL:
        if name != "pension_credit_assessable_capital":
            capital = simulation.calculate(name, YEAR)
            assert list(capital[:2]) == expected_uc[:2], name
    assert list(simulation.calculate("pension_credit_assessable_capital", YEAR)) == [
        0,
        0,
        19_000,
        0,
    ]


money = st.integers(min_value=0, max_value=2_000_000).map(lambda pence: pence / 100)
# One benefit unit: a claimant, perhaps a partner, each with a cash and a
# stocks and shares ISA, and a child; with savings and other shares.
ONE_UNIT_HOUSEHOLDS = st.lists(
    st.tuples(st.lists(st.tuples(money, money), min_size=1, max_size=2), money, money),
    min_size=1,
    max_size=4,
)
# Each example runs whole means tests, so keep the examples few.
DATASET_SETTINGS = settings(SETTINGS, max_examples=3)
SITUATION_SETTINGS = settings(SETTINGS, max_examples=4)


@DATASET_SETTINGS
@given(households=ONE_UNIT_HOUSEHOLDS)
def test_balances_alone_and_totals_alone_give_one_unit_the_same_capital(
    households,
):
    """Invariant 4, differential: the two forms of the same holdings."""
    balances, totals = [], []
    for adults, other_shares, savings in households:
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
            assert balances_only.calculate(name, year) == pytest.approx(
                totals_only.calculate(name, year), rel=1e-6, abs=0.01
            ), (name, year)


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
    person = st.tuples(money, money)
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


def _check_counted_isas(simulation, units, assets):
    """Invariant 2: the household counts min(balances, total) of each kind."""
    totals = {
        "cash_isa_countable_capital": simulation.calculate("cash_isa", YEAR)[0],
        "stocks_and_shares_isa_countable_capital": min(
            simulation.calculate("stocks_and_shares_isa", YEAR)[0],
            simulation.calculate("share_like_capital", YEAR)[0],
        ),
    }
    counted = {}
    for name, total in totals.items():
        balance = simulation.calculate(BALANCE[name], YEAR)
        counted[name] = simulation.calculate(name, YEAR)
        assert (counted[name] >= 0).all()
        assert (counted[name] <= balance * (1 + 1e-6) + 1e-3).all()
        assert counted[name].sum() == pytest.approx(
            min(balance.sum(), max(0, total)), rel=1e-5, abs=0.01
        )
        if balance.sum() > total > 0:
            share = counted[name] / total
            assert share == pytest.approx(balance / balance.sum(), abs=1e-5)
    return counted


def _holdings(simulation):
    return sum(
        simulation.calculate(name, YEAR)[0]
        for name in ("savings", "cash_isa", "share_like_capital")
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
    counted = _check_counted_isas(simulation, units, assets)
    dependants = ~simulation.calculate("is_claimant_or_partner", YEAR)
    uncounted = sum((amount * dependants).sum() for amount in counted.values())
    for name in (
        "uc_assessable_capital",
        "housing_benefit_assessable_capital",
        "income_support_assessable_capital",
        "jsa_income_assessable_capital",
        "esa_income_assessable_capital",
    ):
        capital = simulation.calculate(name, YEAR)
        assert capital.sum() + uncounted == pytest.approx(
            _holdings(simulation), rel=1e-5, abs=0.05
        ), name
        # Each unit counts at least its own claimant's and partner's ISAs.
        own = sum(
            simulation.map_result(amount * ~dependants, "person", "benunit", how="sum")
            for amount in counted.values()
        )
        assert (capital >= own * (1 - 1e-6) - 0.01).all(), name


@SITUATION_SETTINGS
@given(
    pensioners=st.lists(_unit([70, 75]), min_size=1, max_size=2),
    others=st.lists(_unit([30]), min_size=0, max_size=1),
    holdings=HOLDINGS,
)
def test_a_pound_counts_once_in_pension_credit(pensioners, others, holdings):
    """Invariant 1 for Pension Credit, shared by pension-age adults only."""
    units = pensioners + others
    assets = _assets(units, holdings)
    simulation = Simulation(situation=_situation(units, assets))
    counted = _check_counted_isas(simulation, units, assets)
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
    uncounted = sum((amount * ~counts).sum() for amount in counted.values())
    capital = simulation.calculate("pension_credit_assessable_capital", YEAR)
    assert capital.sum() + uncounted == pytest.approx(
        _holdings(simulation), rel=1e-5, abs=0.05
    )


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

    assert capital("uc_assessable_capital") == [1_000, 15_000]
    assert capital("housing_benefit_assessable_capital") == [1_000, 15_000]
    sources = list(_node(uc_path + ".sources")(f"{YEAR}-01-01"))
    # Dropping cash_isa from UC's sources: savings 2,000 shared, and the
    # lodger keeps their 4,000 stocks and shares ISA. Dropping
    # share_like_capital: the 10,000 cash ISA stays theirs.
    for dropped, expected in (
        ("cash_isa", [1_000, 5_000]),
        ("share_like_capital", [1_000, 11_000]),
    ):
        kept = [name for name in sources if name != dropped]
        with _law(simulation, uc_path + ".sources", kept):
            assert capital("uc_assessable_capital") == expected, dropped
    # Emptying UC's person_sources returns both ISAs to the pool: savings
    # 2,000 and the ISAs, 16,000 in all, shared by two claimants. Housing
    # Benefit keeps its own lists.
    with _law(simulation, uc_path + ".person_sources", []):
        assert capital("uc_assessable_capital") == [8_000, 8_000]
        assert capital("housing_benefit_assessable_capital") == [1_000, 15_000]
    assert capital("uc_assessable_capital") == [1_000, 15_000]


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

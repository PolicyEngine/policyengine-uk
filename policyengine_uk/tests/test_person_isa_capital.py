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
"""

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import UKSingleYearDataset
from policyengine_uk.data.economic_assumptions import PROJECTION_END_YEAR
from policyengine_uk.system import system
from policyengine_uk.variables.gov.dwp._person_capital_pool import (
    HOUSEHOLD_SOURCE_OF,
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


money = st.integers(min_value=0, max_value=2_000_000).map(lambda pence: pence / 100)
# One benefit unit: a claimant, perhaps a partner, each with a cash and a
# stocks and shares ISA, and a child; with savings and other shares.
ONE_UNIT_HOUSEHOLDS = st.lists(
    st.tuples(st.lists(st.tuples(money, money), min_size=1, max_size=2), money, money),
    min_size=1,
    max_size=4,
)
DATASET_SETTINGS = settings(SETTINGS, max_examples=3)


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


@SETTINGS
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


@SETTINGS
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


def _uc_sources_without(source):
    path = CAPITAL["uc_assessable_capital"] + ".sources"
    kept = [name for name in _node(path)(f"{YEAR}-01-01") if name != source]
    return {path: {f"{YEAR}-01-01.2100-12-31": kept}}


@pytest.mark.parametrize(
    "source, expected",
    [
        # Cash ISAs disregarded: savings 2,000 shared, and the lodger keeps
        # their 4,000 stocks and shares ISA.
        ("cash_isa", [1_000, 5_000]),
        # Share-like capital disregarded: the 10,000 cash ISA stays theirs.
        ("share_like_capital", [1_000, 11_000]),
    ],
)
def test_a_reform_that_drops_a_household_source_drops_its_person_source(
    source, expected
):
    """Invariant 6: a person ISA counts only while its household source does."""
    reformed = Simulation(situation=LODGER, reform=_uc_sources_without(source))
    assert list(reformed.calculate("uc_assessable_capital", YEAR)) == expected
    baseline = Simulation(situation=LODGER)
    assert list(baseline.calculate("uc_assessable_capital", YEAR)) == [1_000, 15_000]
    assert list(baseline.calculate("housing_benefit_assessable_capital", YEAR)) == [
        1_000,
        15_000,
    ]


def test_emptying_person_sources_returns_the_isas_to_the_pool():
    """Invariant 6: without the person sources the household proxy stands."""
    path = CAPITAL["uc_assessable_capital"] + ".person_sources"
    reformed = Simulation(
        situation=LODGER, reform={path: {f"{YEAR}-01-01.2100-12-31": []}}
    )
    # Savings 2,000 and both ISAs, 16,000 in all, shared by two claimants.
    assert list(reformed.calculate("uc_assessable_capital", YEAR)) == [8_000, 8_000]
    # Housing Benefit keeps its own lists.
    assert list(reformed.calculate("housing_benefit_assessable_capital", YEAR)) == [
        1_000,
        15_000,
    ]


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

"""Share-like capital in the means tests, itemised and valued by asset type.

The capital lists name share_like_capital's two parts:
share_like_capital_with_sale_expenses (directly held shares, and all of an
unitemised corporate_wealth), which the sale-expense lists value less 10%, and
share_like_capital_without_sale_expenses (unit and investment trusts, stocks
and shares ISAs), valued in full.

Invariants:
1. share_like_capital is corporate_wealth as supplied (any sign, any fraction)
   unless the itemised components exceed it beyond the rounding tolerance, in
   which case it is their sum.
2. Where the itemised holdings sum to nil or less, the part with sale
   expenses is all of share_like_capital and the other part is exactly nil;
   otherwise the part with sale expenses is share_like_capital less trusts
   and ISAs, held between nil and share_like_capital. Whatever the signs of
   the holdings, the two parts add up to share_like_capital within half its
   float32 spacing.
3. Differential: for identical unitemised inputs, every programme's assessable
   capital and UC eligibility equal those under the lists before itemising
   (corporate_wealth valued less 10%), exactly, annually and monthly.
4. Split effect: a consistent split raises a working-age single adult's UC
   capital by 10% of trusts plus ISAs, against the unitemised lists.
5. A disregarded company holding (UC reg 77(2)) leaves the UC capital pool
   from the part with sale expenses, whether it was entered within
   corporate_wealth or as directly held shares. A reform that stops UC
   counting that part takes no holding out of the pool, and the owner's own
   assessment still takes the holding off a report.
6. The exempt list exists from the first date any capital list does.
7. Valuation by type: given only itemised holdings, with the ISAs held as the
   person's own balances, the six DWP means tests count savings, cash ISAs,
   unit trusts and stocks and shares ISAs in full and directly held shares
   less 10%, rounded by each programme's rule, to within a penny plus
   float32's step at that size.
8. A reform that removes stocks_and_shares_isa from the exempt list moves a
   member's stocks and shares ISA balance with the household's ISAs into the
   part with sale expenses: the formulas net the balance out of that part
   and count it in the holder's unit less 10%.
9. A person's stocks and shares ISA balance holds no more than the holdings
   behind the part that holds the ISAs (trusts and ISAs while listed, held
   between nil and share_like_capital; the rest of share_like_capital for the
   part with sale expenses), allowing for the one float32 rounding that forms
   them, and all of a balance those holdings cover. Universal Credit counts
   each part on its lists within rounding of the holdings behind it.
"""

from fractions import Fraction

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.variables.household.wealth.share_like_capital import (
    RELATIVE_TOLERANCE,
)

COMPONENTS = (
    "directly_held_shares",
    "unit_and_investment_trusts",
    "stocks_and_shares_isa",
)
WITH, WITHOUT = (
    "share_like_capital_with_sale_expenses",
    "share_like_capital_without_sale_expenses",
)
LEGAL_RATE = 0.1
NODES = {
    "uc_assessable_capital": "gov.dwp.universal_credit.means_test.capital",
    "housing_benefit_assessable_capital": "gov.dwp.housing_benefit.means_test.capital",
    "income_support_assessable_capital": "gov.dwp.income_support.means_test.capital",
    "jsa_income_assessable_capital": "gov.dwp.JSA.income.capital",
    "esa_income_assessable_capital": "gov.dwp.ESA.income.capital",
    "pension_credit_assessable_capital": "gov.dwp.pension_credit.income.capital",
}
YEAR = 2026
SETTINGS = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

system = CountryTaxBenefitSystem()


def _node(path):
    node = system.parameters
    for part in path.split("."):
        node = getattr(node, part)
    return node


def _parameter(path):
    return _node(path)(f"{YEAR}-01-01")


def _unitemised(sources):
    """The list before itemising: corporate_wealth where the share parts are."""
    out = []
    for source in sources:
        if source == WITHOUT:
            continue
        out.append("corporate_wealth" if source == WITH else source)
    return out


UNITEMISED_REFORM = {
    f"{node}.{name}": {str(YEAR): _unitemised(_parameter(f"{node}.{name}"))}
    for node in NODES.values()
    for name in ("sources", "sale_expenses.sources")
}

# Pounds and pence, as a dataset stores them in float64; the engine rounds
# each to float32, which is the rounding the tolerance has to absorb.
money = st.integers(min_value=0, max_value=20_000_000).map(lambda pence: pence / 100)
signed_money = st.integers(min_value=-500_000, max_value=20_000_000).map(
    lambda pence: pence / 100
)


def _situation(households, age=None):
    people, benunits, hhs = {}, {}, {}
    for i, assets in enumerate(households):
        people[f"p{i}"] = {"age": {YEAR: age or (70 if i % 2 else 30)}}
        benunits[f"b{i}"] = {"members": [f"p{i}"], "would_claim_uc": {YEAR: True}}
        hhs[f"h{i}"] = {
            "members": [f"p{i}"],
            **{name: {YEAR: float(value)} for name, value in assets.items()},
        }
    return {"people": people, "benunits": benunits, "households": hhs}


def _results(households, reform=None, period=YEAR, age=None):
    sim = Simulation(situation=_situation(households, age), reform=reform)
    out = {v: sim.calculate(v, period) for v in NODES}
    out["is_uc_eligible"] = sim.calculate("is_uc_eligible", period)
    for v in ("share_like_capital", WITH, WITHOUT):
        out[v] = sim.calculate(v, YEAR)
    return out


@pytest.mark.parametrize("variable", NODES)
def test_lists_name_the_two_parts(variable):
    sources = list(_parameter(f"{NODES[variable]}.sources"))
    sale = list(_parameter(f"{NODES[variable]}.sale_expenses.sources"))
    assert WITH in sources and WITHOUT in sources
    assert not {"corporate_wealth", "share_like_capital", *COMPONENTS} & set(sources)
    assert WITH in sale and WITHOUT not in sale
    assert not {"corporate_wealth", *COMPONENTS} & set(sale)
    # Deposit balances have no costs of sale (ADM H1607, H1675).
    assert "cash_isa" in sources and not {"savings", "cash_isa"} & set(sale)
    without = set(_parameter("gov.dwp.share_like_capital.without_sale_expenses"))
    assert without == {"unit_and_investment_trusts", "stocks_and_shares_isa"}


@SETTINGS
@given(
    st.lists(
        st.tuples(
            signed_money,
            st.tuples(signed_money, signed_money, signed_money),
            st.booleans(),
        ),
        min_size=1,
        max_size=40,
    )
)
# Subtracting trusts and ISA one at a time leaves £0.015625 here; grouped, nil.
@example([(399_999.984375, (0.0, 200_000.0, 199_999.984375), True)])
# Trusts and ISA exceed corporate_wealth by float32 rounding: floored at nil.
@example([(16_000.0, (0.0, 8_000.01, 8_000.0), True)])
# Shares of £1 billion, trusts of -£1 billion and a £1 ISA itemise £1, and
# trusts and ISA come to -£1 billion in float32. Floored at nil alone, the
# part with sale expenses would hold £1 billion and the other -£1 billion,
# which add up to nil; capped at the £1 total, it holds £1 and the other nil.
@example([(0.0, (1_000_000_000.0, -1_000_000_000.0, 1.0), True)])
def test_share_like_capital_and_its_parts(rows):
    households = []
    for corporate_wealth, components, itemise in rows:
        assets = {"corporate_wealth": corporate_wealth}
        if itemise:
            assets |= dict(zip(COMPONENTS, components))
        households.append(assets)
    got = _results(households)
    for i, assets in enumerate(households):
        cw = np.float32(assets["corporate_wealth"])
        values = [np.float32(assets.get(c, 0)) for c in COMPONENTS]
        # The engine's float32 grouping: components added left to right, the
        # exempt holdings summed before they are subtracted.
        itemised = np.float32(np.float32(values[0] + values[1]) + values[2])
        exempt = np.float32(values[1] + values[2])
        tolerance = RELATIVE_TOLERANCE * max(abs(cw), itemised)
        share_like = got["share_like_capital"][i]
        if itemised > 0 and itemised - cw > tolerance:
            assert share_like == itemised
        else:
            assert share_like == cw
        if itemised <= 0:
            assert got[WITH][i] == share_like and got[WITHOUT][i] == 0
        else:
            assert got[WITH][i] == min(
                share_like, max(np.float32(0), np.float32(share_like - exempt))
            )
            assert got[WITHOUT][i] == np.float32(share_like - got[WITH][i])
        # The parts add up to the total within half its float32 spacing:
        # the part without sale expenses rounds once, and it is no larger
        # than the total.
        gap = (
            Fraction(float(got[WITH][i]))
            + Fraction(float(got[WITHOUT][i]))
            - Fraction(float(share_like))
        )
        assert abs(gap) <= Fraction(float(np.spacing(np.abs(share_like)))) / 2


def test_float32_grouping_of_the_exempt_holdings():
    """Trusts and ISA summed first: corporate_wealth of £399,999.984375 and
    £200,000 + £199,999.984375 of exempt holdings both round to £400,000 in
    float32, so the part with sale expenses is nil; subtracting the two one at
    a time would leave £0.015625."""
    households = [
        {
            "corporate_wealth": 399_999.984375,
            "unit_and_investment_trusts": 200_000,
            "stocks_and_shares_isa": 199_999.984375,
        }
    ]
    got = _results(households)
    assert got[WITH][0] == 0


def test_exempt_holdings_above_the_aggregate_by_rounding_leave_nil_with_expenses():
    """£8,000.01 of trusts and an £8,000 ISA add up in float32 to
    £16,000.009765625, above £16,000 of corporate_wealth by less than a
    millionth, so share_like_capital keeps the £16,000. Subtracting the exempt
    holdings would leave -£0.009765625; the part with sale expenses stops at
    nil, and the part without holds all £16,000."""
    households = [
        {
            "corporate_wealth": 16_000,
            "unit_and_investment_trusts": 8_000.01,
            "stocks_and_shares_isa": 8_000,
        }
    ]
    got = _results(households)
    assert got["share_like_capital"][0] == 16_000
    assert got[WITH][0] == 0 and got[WITHOUT][0] == 16_000


def test_an_empty_exempt_list_values_everything_less_10_percent():
    """A ruling that every share-like holding takes the 10% is a parameter edit."""
    reform = {"gov.dwp.share_like_capital.without_sale_expenses": {str(YEAR): []}}
    households = [
        {"savings": 1_000, "corporate_wealth": 12_000},
        {
            "savings": 1_000,
            "directly_held_shares": 4_000,
            "unit_and_investment_trusts": 3_000,
            "stocks_and_shares_isa": 5_000,
        },
    ]
    got = _results(households, reform=reform, age=30)
    assert list(got[WITH]) == [12_000, 12_000]
    assert list(got[WITHOUT]) == [0, 0]
    # £1,000 + 90% of £12,000 either way.
    assert got["uc_assessable_capital"] == pytest.approx([11_800, 11_800])


# The ISAs take the deduction; unit and investment trusts keep full value.
ISAS_WITH_SALE_EXPENSES = {
    "gov.dwp.share_like_capital.without_sale_expenses": {
        str(YEAR): ["unit_and_investment_trusts"]
    }
}
WORKING_AGE = [name for name in NODES if name != "pension_credit_assessable_capital"]


def _isa_holders():
    """A sole working-age holder of a £5,000 stocks and shares ISA; a tenant
    and a lodger in separate benefit units sharing £1,000 of savings, the
    lodger holding a £5,000 ISA; and a sole pension-age holder of a £5,000
    ISA. The ISAs are person balances, with no household total stored, and
    no unit claims a passporting benefit."""
    people = {
        "holder": {"age": {YEAR: 30}},
        "tenant": {"age": {YEAR: 30}},
        "lodger": {"age": {YEAR: 30}},
        "pensioner": {"age": {YEAR: 70}},
    }
    for name in ("holder", "lodger", "pensioner"):
        people[name]["stocks_and_shares_isa_balance"] = {YEAR: 5_000}
    no_claims = {
        "would_claim_uc": {YEAR: False},
        "would_claim_IS": {YEAR: False},
        "would_claim_pc": {YEAR: False},
    }
    return {
        "people": people,
        "benunits": {
            f"{name}_unit": {"members": [name], **no_claims} for name in people
        },
        "households": {
            "alone": {"members": ["holder"]},
            "shared": {"members": ["tenant", "lodger"], "savings": {YEAR: 1_000}},
            "retired": {"members": ["pensioner"]},
        },
    }


def test_a_reform_that_takes_isas_out_of_the_exempt_list_values_person_isas_less_10_percent():
    """Each household's share_like_capital is its £5,000 of ISAs, the sum of
    the balances. At baseline the part without sale expenses holds it, and
    the holder counts the balance in full: £5,000 alone, and in the shared
    household £500 of the savings each and the lodger's £5,000, so
    [£500, £5,500].

    Without stocks_and_shares_isa on the exempt list, the part with sale
    expenses holds the £5,000 and the balance leaves that part, so the pool
    keeps nil of it. The holder counts 90% of the £5,000, £4,500. In the
    shared household the pool keeps the £1,000 of savings, £500 for each
    unit, and the lodger adds £4,500: [£500, £5,000]. Netting the balance
    out of the empty part without sale expenses instead would give the sole
    holder £5,000 (a pool of £4,500 less £5,000, floored at nil, plus the
    balance in full) and the shared household [£250, £5,250] (a pool of
    £1,000 + £4,500 - £5,000 = £500, then the balance in full).
    """
    baseline = Simulation(situation=_isa_holders())
    reformed = Simulation(situation=_isa_holders(), reform=ISAS_WITH_SALE_EXPENSES)
    assert list(baseline.calculate(WITHOUT, YEAR)) == [5_000, 5_000, 5_000]
    assert list(reformed.calculate(WITH, YEAR)) == [5_000, 5_000, 5_000]
    assert list(reformed.calculate(WITHOUT, YEAR)) == [0, 0, 0]
    for simulation in (baseline, reformed):
        assert list(
            simulation.calculate("stocks_and_shares_isa_countable_capital", YEAR)
        ) == [5_000, 0, 5_000, 5_000]
    # Units: holder, tenant, lodger, pensioner.
    for name in WORKING_AGE:
        assert list(baseline.calculate(name, YEAR)[:3]) == [5_000, 500, 5_500], name
        assert list(reformed.calculate(name, YEAR)[:3]) == [4_500, 500, 5_000], name
    pension_credit = "pension_credit_assessable_capital"
    assert baseline.calculate(pension_credit, YEAR)[3] == 5_000
    assert reformed.calculate(pension_credit, YEAR)[3] == 4_500


def test_the_part_holding_the_isas_bounds_balances_only_beyond_rounding():
    """A sole holder's £100.01 ISA balance inside £20,000.01 of
    corporate_wealth: the part with sale expenses is £19,900.00 in float32,
    and the part without it, the difference, 100.009765625, a quarter of a
    thousandth short of the 100.01000214 balance. That is rounding: the
    listed holdings behind the part, the £100.01 ISA, cover the balance, so
    the holder keeps the whole balance, as before the part bounded it: UC counts
    90% of £19,900, £17,910, plus the part less the balance, plus the
    balance, £18,010.01.

    Trusts of -£5,000 beside £6,000 of shares and a lodger's £5,000 ISA
    leave share_like_capital at £6,000, all in the part with sale expenses,
    and nil in the part that would hold the ISA: trusts and ISA sum to nil.
    The balance can't take
    £5,000 out of nil, so the lodger holds nil, and the pool counts 90% of
    £6,000, £5,400, shared by two units: [£2,700, £2,700]. Netting £5,000 out
    of the empty part would give [£200, £5,200]."""
    situation = {
        "people": {
            "holder": {
                "age": {YEAR: 30},
                "stocks_and_shares_isa_balance": {YEAR: 100.01},
            },
            "tenant": {"age": {YEAR: 30}},
            "lodger": {
                "age": {YEAR: 30},
                "stocks_and_shares_isa_balance": {YEAR: 5_000},
            },
        },
        "benunits": {
            f"{name}_unit": {"members": [name]}
            for name in ("holder", "tenant", "lodger")
        },
        "households": {
            "rounding": {
                "members": ["holder"],
                "corporate_wealth": {YEAR: 20_000.01},
            },
            "signed": {
                "members": ["tenant", "lodger"],
                "directly_held_shares": {YEAR: 6_000},
                "unit_and_investment_trusts": {YEAR: -5_000},
            },
        },
    }
    sim = Simulation(situation=situation)
    assert list(sim.calculate(WITH, YEAR)) == [19_900, 6_000]
    assert list(sim.calculate(WITHOUT, YEAR)) == [np.float32(100.009765625), 0]
    held = sim.calculate("stocks_and_shares_isa_countable_capital", YEAR)
    assert list(held) == [np.float32(100.01), 0, 0]
    uc = sim.calculate("uc_assessable_capital", YEAR)
    assert list(uc) == [np.float32(18_010.01), 2_700, 2_700]


UC_NODE = NODES["uc_assessable_capital"]


def _uc_lists_without(part):
    """A reform that drops ``part`` from UC's capital and sale-expense lists."""
    return {
        f"{UC_NODE}.{name}": {
            str(YEAR): [
                source for source in _parameter(f"{UC_NODE}.{name}") if source != part
            ]
        }
        for name in ("sources", "sale_expenses.sources")
    }


def _sole_isa_holders(rows):
    """One working-age adult per household and benefit unit, with
    corporate_wealth, directly held shares and unit trusts on the household
    and a stocks and shares ISA balance on the person, no household ISA total
    stored, so stocks_and_shares_isa is the balance."""
    people, benunits, homes = {}, {}, {}
    for i, (corporate_wealth, shares, trusts, balance) in enumerate(rows):
        people[f"p{i}"] = {
            "age": {YEAR: 30},
            "stocks_and_shares_isa_balance": {YEAR: float(balance)},
        }
        benunits[f"b{i}"] = {"members": [f"p{i}"]}
        homes[f"h{i}"] = {
            "members": [f"p{i}"],
            "corporate_wealth": {YEAR: float(corporate_wealth)},
            "directly_held_shares": {YEAR: float(shares)},
            "unit_and_investment_trusts": {YEAR: float(trusts)},
        }
    return {"people": people, "benunits": benunits, "households": homes}


def test_a_balance_counts_nothing_the_holdings_behind_its_part_do_not_hold():
    """Review r2's witness and two like it, where the holdings behind the
    part that holds the ISAs come to nil although share_like_capital's
    float32 spacing is at least the £1 balance.

    1. Shares of £8,388,608 (2**23), trusts of -£1 and a £1 ISA balance:
       the itemised sum is £8,388,608, so share_like_capital is £8,388,608.
       Trusts and ISA sum to exactly nil, so the part with sale expenses is
       £8,388,608, the part without nil, and the balance holds nil. With the
       part with sale expenses off UC's lists, UC counts nothing; bounded by
       the smaller of the ISA total and share_like_capital, the £1 would be
       netted from the empty part, floored at nil, and counted: £1.
    2. corporate_wealth of £16,777,216 (2**24), shares of -£2 and a £1 ISA
       balance: the itemised sum is -£1, so share_like_capital is the
       £16,777,216, all of it in the part with sale expenses, and the
       balance holds nil. With that part off UC's lists, UC counts nothing.
    3. With stocks_and_shares_isa off the exempt list, shares of -£1, trusts
       of £8,388,608 and a £1 ISA balance: share_like_capital is £8,388,608,
       all of it trusts, so the part with sale expenses, which now holds the
       ISAs, is nil, and the balance holds nil. With the part without sale
       expenses off UC's lists, UC counts nothing, not 90% of £1.

    UC at baseline is 90% of share_like_capital in cases 1 and 2,
    £7,549,747.20 and £15,099,494.40, which float32 holds as £7,549,747 and
    £15,099,494, and in case 3 under the exempt-list reform alone the
    £8,388,608 of trusts in full."""
    rows = [(0, 2**23, -1, 1), (2**24, -2, 0, 1)]
    baseline = Simulation(situation=_sole_isa_holders(rows))
    reformed = Simulation(
        situation=_sole_isa_holders(rows), reform=_uc_lists_without(WITH)
    )
    for sim in (baseline, reformed):
        assert list(sim.calculate("share_like_capital", YEAR)) == [2**23, 2**24]
        assert list(sim.calculate(WITH, YEAR)) == [2**23, 2**24]
        assert list(sim.calculate(WITHOUT, YEAR)) == [0, 0]
        held = sim.calculate("stocks_and_shares_isa_countable_capital", YEAR)
        assert list(held) == [0, 0]
    assert list(baseline.calculate("uc_assessable_capital", YEAR)) == [
        np.float32(7_549_747.2),
        np.float32(15_099_494.4),
    ]
    assert list(reformed.calculate("uc_assessable_capital", YEAR)) == [0, 0]

    mirror = _sole_isa_holders([(0, -1, 2**23, 1)])
    exempt_list = ISAS_WITH_SALE_EXPENSES
    for reform, uc in (
        (exempt_list, 2**23),
        ({**exempt_list, **_uc_lists_without(WITHOUT)}, 0),
    ):
        sim = Simulation(situation=mirror, reform=reform)
        assert sim.calculate(WITH, YEAR)[0] == 0
        assert sim.calculate(WITHOUT, YEAR)[0] == 2**23
        assert sim.calculate("stocks_and_shares_isa_countable_capital", YEAR)[0] == 0
        assert sim.calculate("uc_assessable_capital", YEAR)[0] == uc


def _exact(value):
    return Fraction(float(value))


# Signed holdings at and beside powers of two, where share_like_capital's
# float32 spacing is a hundredth of a penny (2**10), £1 (2**23), £2 (2**24)
# and £4 (2**25), and balances of a few pounds up to the power itself.
SWEEP = [
    (corporate_wealth, shares, trusts, balance)
    for power in (2.0, 2.0**10, 2.0**23, 2.0**24, 2.0**25)
    for corporate_wealth in (0, power)
    for shares in (0, power, power - 1, -1, -2, -power)
    for trusts in (0, power, power - 1, -1, -2, -power)
    for balance in (1, 2, 3, power)
]


@pytest.mark.parametrize("isas_exempt", [True, False])
def test_isa_balances_stay_within_the_holdings_behind_their_part(isas_exempt):
    """Invariant 9, swept over SWEEP with the ISAs in each part, and UC
    counting both parts, only the part without sale expenses, and only the
    part with them.

    Worked in exact arithmetic from the float32 holdings: the holdings behind
    the part that holds the ISAs are, where the itemised sum is positive, the
    listed holdings' sum (trusts, and the ISA while it is listed) held
    between nil and share_like_capital, or for the part with sale expenses
    share_like_capital less that; otherwise nil, or all of
    share_like_capital. The engine forms them with one float32 rounding, of
    the listed sum or of share_like_capital less it. Then:
    - the balance holds between nil and the smaller of itself and
      share_like_capital, and within that rounding of the smaller of those
      and the holdings, so it holds all of a balance the holdings cover;
    - each part lies within share_like_capital's float32 spacing plus the
      listed sum's rounding of the holdings behind it;
    - UC counts each part on its lists at its value there, within the parts'
      and the balance's rounding, a penny for each valuation, and float32's
      step at the result.
    """
    exempt = {} if isas_exempt else ISAS_WITH_SALE_EXPENSES
    situation = _sole_isa_holders(SWEEP)
    holder_part = WITHOUT if isas_exempt else WITH
    for counted in ((WITH, WITHOUT), (WITHOUT,), (WITH,)):
        dropped = {WITH, WITHOUT} - set(counted)
        reform = dict(exempt)
        for part in dropped:
            reform |= _uc_lists_without(part)
        sim = Simulation(situation=situation, reform=reform or None)
        share_like = sim.calculate("share_like_capital", YEAR)
        isa_total = sim.calculate("stocks_and_shares_isa", YEAR)
        parts = {name: sim.calculate(name, YEAR) for name in (WITH, WITHOUT)}
        held = sim.calculate("stocks_and_shares_isa_countable_capital", YEAR)
        uc = sim.calculate("uc_assessable_capital", YEAR)
        for i, (_, shares, trusts, balance) in enumerate(SWEEP):
            row = (SWEEP[i], isas_exempt, counted)
            values = [np.float32(v) for v in (shares, trusts, balance)]
            itemised = np.float32(np.float32(values[0] + values[1]) + values[2])
            listed = values[1:] if isas_exempt else values[1:2]
            listed_sum = sum(_exact(v) for v in listed)
            # The engine adds the listed holdings from nil, left to right.
            engine_sum = np.float32(0)
            for value in listed:
                engine_sum = np.float32(engine_sum + value)
            sum_rounding = abs(_exact(engine_sum) - listed_sum)
            total = _exact(share_like[i])
            if itemised > 0:
                behind = {WITHOUT: min(total, max(0, listed_sum))}
                behind[WITH] = total - behind[WITHOUT]
                rounding = (
                    sum_rounding
                    if isas_exempt
                    else abs(
                        _exact(np.float32(share_like[i] - engine_sum))
                        - (total - _exact(engine_sum))
                    )
                    + sum_rounding
                )
            else:
                behind = {WITHOUT: Fraction(0), WITH: total}
                rounding = Fraction(0)
            cap = max(Fraction(0), min(_exact(isa_total[i]), total))
            holding = _exact(held[i])
            assert 0 <= holding <= cap, row
            assert abs(holding - min(cap, max(0, behind[holder_part]))) <= rounding, row
            if behind[holder_part] >= cap:
                assert holding == cap, row
            spacing = _exact(np.spacing(np.abs(share_like[i])))
            # The part without sale expenses is share_like_capital less the
            # other part: less than share_like_capital's spacing either side
            # of the engine's clamped listed sum, which bounds the balances.
            engine_behind = (
                min(total, max(0, _exact(engine_sum))) if itemised > 0 else 0
            )
            assert abs(_exact(parts[WITHOUT][i]) - engine_behind) < max(
                spacing, Fraction(2) ** -149
            ), row
            for name in (WITH, WITHOUT):
                assert abs(_exact(parts[name][i]) - behind[name]) <= (
                    spacing + sum_rounding
                ), (row, name)
            sale = set(_parameter(f"{UC_NODE}.sale_expenses.sources")) - dropped
            value = {
                name: Fraction(9, 10) if name in sale else Fraction(1)
                for name in counted
            }
            expected = sum(value[name] * behind[name] for name in counted)
            tolerance = (
                sum(abs(_exact(parts[name][i]) - behind[name]) for name in counted)
                + rounding
                + Fraction(3, 100)
                + _exact(np.spacing(np.float32(float(expected))))
            )
            assert abs(_exact(uc[i]) - expected) <= tolerance, (row, uc[i], expected)


def test_the_exempt_list_starts_with_the_first_capital_list():
    exempt = system.parameters.gov.dwp.share_like_capital.without_sale_expenses
    first = min(
        min(entry.instant_str for entry in _node(f"{node}.sources").values_list)
        for node in NODES.values()
    )
    assert first == "1996-10-07"
    assert min(entry.instant_str for entry in exempt.values_list) == first


@pytest.mark.parametrize(
    "variable", ["income_support_assessable_capital", "jsa_income_assessable_capital"]
)
def test_legacy_capital_before_universal_credit(variable):
    """2012: the legacy lists apply, and so does the exempt list (from 1996)."""
    situation = _situation([{"savings": 1_000, "corporate_wealth": 12_000}], age=30)
    for entity in situation.values():
        for name, values in entity.items():
            for key, by_year in list(values.items()):
                if isinstance(by_year, dict) and YEAR in by_year:
                    values[key] = {2012: by_year[YEAR]}
    capital = Simulation(situation=situation).calculate(variable, 2012)[0]
    assert capital == pytest.approx(11_800)


@SETTINGS
@given(
    st.lists(st.tuples(money, signed_money), min_size=1, max_size=30),
)
def test_unitemised_inputs_match_the_lists_before_itemising(rows):
    households = [{"savings": s, "corporate_wealth": cw} for s, cw in rows]
    households += [
        {"savings": 6_001, "corporate_wealth": -2},
        {"savings": 0, "corporate_wealth": 17_777.78},  # 90% is £16,000.002
    ]
    # A projected year as well, where the inputs are uprated.
    for period in (YEAR, f"{YEAR}-01", YEAR + 1, f"{YEAR + 1}-01"):
        new = _results(households, period=period)
        old = _results(households, reform=UNITEMISED_REFORM, period=period)
        for variable in (*NODES, "is_uc_eligible"):
            assert np.array_equal(new[variable], old[variable]), (variable, period)


@SETTINGS
@given(
    st.lists(st.tuples(money, st.tuples(money, money, money)), min_size=1, max_size=30)
)
def test_a_consistent_split_exempts_trusts_and_isas(rows):
    households = [
        {
            "savings": savings,
            "corporate_wealth": float(sum(components)),
            **dict(zip(COMPONENTS, components)),
        }
        for savings, components in rows
    ]
    new = _results(households, age=30)
    old = _results(households, reform=UNITEMISED_REFORM, age=30)
    for i, (_, (_, trusts, isa)) in enumerate(rows):
        exempt = np.float32(trusts) + np.float32(isa)
        assert new["uc_assessable_capital"][i] - old["uc_assessable_capital"][
            i
        ] == pytest.approx(LEGAL_RATE * exempt, rel=1e-5, abs=0.05)
    # Uprated separately in float32, the components still round to their
    # aggregate in a projected year, so share-like capital is the aggregate.
    sim = Simulation(situation=_situation(households, age=30))
    for year in (YEAR, YEAR + 1):
        assert np.array_equal(
            sim.calculate("share_like_capital", year),
            sim.calculate("corporate_wealth", year),
        ), year


def test_components_alone_are_valued_by_type():
    households = [
        {
            "savings": 1_000,
            "directly_held_shares": 4_000,
            "unit_and_investment_trusts": 3_000,
            "stocks_and_shares_isa": 5_000,
        }
    ]
    got = _results(households, age=30)
    assert got["share_like_capital"][0] == 12_000
    assert got[WITH][0] == 4_000 and got[WITHOUT][0] == 8_000
    # £1,000 + 90% of £4,000 + £3,000 + £5,000.
    assert got["uc_assessable_capital"][0] == pytest.approx(12_600)


def test_a_component_penny_at_the_limit_counts():
    """A penny of shares with no corporate_wealth counts like a penny of it."""
    as_component = [{"savings": 16_000, "directly_held_shares": 0.01}]
    as_aggregate = [{"savings": 16_000, "corporate_wealth": 0.01}]
    for period in (YEAR, f"{YEAR}-01"):
        component = _results(as_component, period=period, age=30)
        aggregate = _results(as_aggregate, period=period, age=30)
        assert component["share_like_capital"][0] == np.float32(0.01)
        for variable in (*NODES, "is_uc_eligible"):
            assert np.array_equal(component[variable], aggregate[variable]), variable
        assert not component["is_uc_eligible"][0]


def test_a_genuine_excess_over_the_aggregate_counts():
    """Ten pence of components above the aggregate is a holding, not rounding."""
    households = [
        {
            "corporate_wealth": 16_000,
            "directly_held_shares": 10_000.10,
            "stocks_and_shares_isa": 6_000,
        }
    ]
    assert _results(households)["share_like_capital"][0] == np.float32(16_000.10)


def test_float32_rounding_at_the_limit_keeps_the_aggregate():
    """Components whose float32 sum overshoots £16,000 by a fraction of a
    penny keep the aggregate; an unitemised penny at the limit counts as
    before itemising."""
    split = [
        {
            "corporate_wealth": 16_000,
            "directly_held_shares": 6_744.81,
            "unit_and_investment_trusts": 6_581.24,
            "stocks_and_shares_isa": 2_673.95,
        }
    ]
    itemised = np.float32(
        np.float32(np.float32(6_744.81) + np.float32(6_581.24)) + np.float32(2_673.95)
    )
    assert itemised > np.float32(16_000)
    assert _results(split)["share_like_capital"][0] == 16_000
    unitemised = [
        {"savings": 15_999.99, "corporate_wealth": 0.01},
        {"savings": 6_001, "corporate_wealth": -2},
    ]
    for period in (YEAR, f"{YEAR}-01"):
        new = _results(unitemised, period=period)
        old = _results(unitemised, reform=UNITEMISED_REFORM, period=period)
        for variable in (*NODES, "is_uc_eligible"):
            assert np.array_equal(new[variable], old[variable]), (variable, period)


def test_one_unit_of_float32_rounding_above_a_power_of_two_keeps_the_aggregate():
    """Pence-valued components whose float32 sum lands one unit in the last place
    (£0.00195) above £16,384.01: more than 1e-7 of the value, less than 1e-6."""
    households = [
        {
            "corporate_wealth": 16_384.01,
            "directly_held_shares": 16_015.98,
            "unit_and_investment_trusts": 286.98,
            "stocks_and_shares_isa": 81.05,
        }
    ]
    itemised = np.float32(
        np.float32(np.float32(16_015.98) + np.float32(286.98)) + np.float32(81.05)
    )
    assert itemised - np.float32(16_384.01) == np.float32(0.001953125)
    assert _results(households)["share_like_capital"][0] == np.float32(16_384.01)


def test_a_disregarded_company_holding_leaves_the_part_with_sale_expenses():
    """UC reg 77(2): the owner's £30,000 holding leaves the pool at the 90% its
    shares are counted at, whether it was entered within corporate_wealth or
    as directly held shares. Two unreported adults share £10,000 of savings."""
    from policyengine_uk.variables.gov.dwp.universal_credit.household_uc_company_holding_pool_scale import (
        HOLDINGS_SOURCE,
    )

    node = NODES["uc_assessable_capital"]
    assert HOLDINGS_SOURCE in _parameter(f"{node}.sources")
    assert HOLDINGS_SOURCE in _parameter(f"{node}.sale_expenses.sources")
    for shares in ({"corporate_wealth": 30_000}, {"directly_held_shares": 30_000}):
        situation = {
            "people": {
                "owner": {
                    "age": {YEAR: 40},
                    "stands_as_sole_owner_or_partner_of_company": {YEAR: True},
                    "owned_company_carries_on_trade": {YEAR: True},
                    "owned_company_holding_value": {YEAR: 30_000},
                },
                "lodger": {"age": {YEAR: 30}},
            },
            "benunits": {
                "owner_unit": {"members": ["owner"]},
                "lodger_unit": {"members": ["lodger"]},
            },
            "households": {
                "household": {
                    "members": ["owner", "lodger"],
                    "savings": {YEAR: 10_000},
                    **{name: {YEAR: value} for name, value in shares.items()},
                }
            },
        }
        sim = Simulation(situation=situation)
        assert sim.calculate("household_uc_company_holding_pool_scale", YEAR)[0] == 1
        # The pool counts the shares at 90%, and the holding leaves it at that.
        assert sim.calculate("household_uc_pool_company_holdings", YEAR)[0] == 27_000
        assert list(sim.calculate("uc_assessable_capital", YEAR)) == [5_000, 5_000]


def test_a_holding_leaves_no_pool_that_stops_counting_the_part_with_sale_expenses():
    """UC reg 77(2), after a reform drops share_like_capital_with_sale_expenses
    from UC's sources and sale-expense list. The household holds £30,000 of
    directly held shares and £10,000 of unit trusts, so the part with sale
    expenses is £30,000 and the part without £10,000. The owner's £30,000
    holding is shares, inside the part the pool no longer counts, so none of
    it leaves the pool: the pool is the £10,000 of trusts at full value,
    £5,000 for the owner's unit and £5,000 for the lodger's. Budgeted against
    the uncounted part, the holding would take all £10,000 of trusts out of
    the pool and leave both units nil.

    With a £40,000 report for the owner's unit, the owner's own assessment
    still takes the £30,000 holding off it, £10,000, and the report consumes
    the £10,000 pool, leaving the lodger nil."""
    node = NODES["uc_assessable_capital"]
    reform = {
        f"{node}.{name}": {
            str(YEAR): [
                source for source in _parameter(f"{node}.{name}") if source != WITH
            ]
        }
        for name in ("sources", "sale_expenses.sources")
    }
    for report, expected in ((None, [5_000, 5_000]), (40_000, [10_000, 0])):
        owner_unit = {"members": ["owner"]}
        if report is not None:
            owner_unit["benunit_reported_capital"] = {YEAR: report}
        situation = {
            "people": {
                "owner": {
                    "age": {YEAR: 40},
                    "stands_as_sole_owner_or_partner_of_company": {YEAR: True},
                    "owned_company_carries_on_trade": {YEAR: True},
                    "owned_company_holding_value": {YEAR: 30_000},
                },
                "lodger": {"age": {YEAR: 30}},
            },
            "benunits": {
                "owner_unit": owner_unit,
                "lodger_unit": {"members": ["lodger"]},
            },
            "households": {
                "household": {
                    "members": ["owner", "lodger"],
                    "directly_held_shares": {YEAR: 30_000},
                    "unit_and_investment_trusts": {YEAR: 10_000},
                }
            },
        }
        sim = Simulation(situation=situation, reform=reform)
        assert sim.calculate(WITH, YEAR)[0] == 30_000
        assert sim.calculate(WITHOUT, YEAR)[0] == 10_000
        assert sim.calculate("household_uc_company_holding_pool_scale", YEAR)[0] == 0
        assert sim.calculate("household_uc_pool_company_holdings", YEAR)[0] == 0
        assert list(sim.calculate("uc_assessable_capital", YEAR)) == expected, report


ROUNDS_DOWN = {
    "uc_assessable_capital": False,
    "housing_benefit_assessable_capital": False,
    "income_support_assessable_capital": True,
    "jsa_income_assessable_capital": True,
    "esa_income_assessable_capital": True,
    "pension_credit_assessable_capital": True,
}
pennies = st.integers(min_value=0, max_value=2_000_000)


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(
    st.lists(
        st.tuples(
            pennies,
            pennies,
            pennies,
            pennies,
            pennies,
            st.sampled_from([30, 70]),
            st.booleans(),
        ),
        min_size=1,
        max_size=20,
    )
)
# £1,000 of savings, £3,000 in a cash ISA, £3,000 of unit trusts and a £5,000
# stocks-and-shares ISA in full, and 90% of £4,000 of shares: £15,600.
@example([(100_000, 300_000, 400_000, 300_000, 500_000, 30, False)])
# Income Support counts £16,834.13 here. The engine gives £16,834.12, held
# in float32 as 16,834.119: £0.0109 under, or £0.0117 when the comparison
# itself runs in float32.
@example([(510_510, 1_046_019, 2_051, 437, 124_602, 30, True)])
# Income Support counts £37,747.34 here, and the engine holds £37,747.33 as
# 37,747.328: £0.0119 under, a penny plus half of float32's step at that
# size (£0.0039).
@example([(1_813_184, 40_164, 988_571, 7_260, 1_024_413, 30, False)])
def test_itemised_holdings_are_valued_by_type_in_every_means_test(rows):
    """Given only itemised holdings, with the ISAs held as the person's own
    balances, each of the six DWP means tests counts savings, a cash ISA, unit
    trusts and a stocks-and-shares ISA in full and directly held shares less
    10%, rounded by the programme's rule. The engine adds the holdings in
    float32, which can move the shares' value by a fraction of a penny before
    valuation, so each total is checked to within a penny plus float32's step
    at that size."""
    people, benunits, homes = {}, {}, {}
    for i, (savings, cash_isa, shares, trusts, isa, age, claims_uc) in enumerate(rows):
        people[f"p{i}"] = {
            "age": {YEAR: age},
            "cash_isa_balance": {YEAR: cash_isa / 100},
            "stocks_and_shares_isa_balance": {YEAR: isa / 100},
        }
        benunits[f"b{i}"] = {
            "members": [f"p{i}"],
            "would_claim_uc": {YEAR: claims_uc},
        }
        homes[f"h{i}"] = {
            "members": [f"p{i}"],
            "savings": {YEAR: savings / 100},
            "directly_held_shares": {YEAR: shares / 100},
            "unit_and_investment_trusts": {YEAR: trusts / 100},
        }
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": homes}
    )
    passported = sim.calculate("housing_benefit_on_passporting_benefit", YEAR)
    for variable, round_down in ROUNDS_DOWN.items():
        values = sim.calculate(variable, YEAR)
        for i, (savings, cash_isa, shares, trusts, isa, age, _) in enumerate(rows):
            if variable == "pension_credit_assessable_capital":
                if age < 67:
                    continue
            elif age >= 67 or (
                variable == "housing_benefit_assessable_capital" and passported[i]
            ):
                continue
            share_pence = (9 * shares + (0 if round_down else 5)) // 10
            expected = (savings + cash_isa + trusts + isa + share_pence) / 100
            tolerance = 0.01 + float(np.spacing(np.float32(expected)))
            assert abs(float(values[i]) - expected) <= tolerance, (
                variable,
                rows[i],
                values[i],
            )

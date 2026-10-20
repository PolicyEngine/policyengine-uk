"""IIDB, SDA, incapacity benefit and war pensions in Council Tax Reduction income.

Council Tax Reduction income left out industrial injuries disablement benefit
(IIDB), severe disablement allowance (SDA) and incapacity benefit (IB), which
every scheme the model runs counts:

- England, pensioners: SI 2012/2885 Sch 1 para 16(1)(j), social security
  benefits other than those it lists; (j)(v) excepts only IIDB's increases
  under SSCBA 1992 ss.104 and 105.
- English working-age schemes: gross income (SI 2012/2886 Sch para 54(1))
  less Sch 8, which disregards none of the three; Kingston upon Thames, Merton
  and Newham copy it, and Oxford counts income other than earnings unless its
  Appendix 5 lists it.
- Wales: WSI 2013/3029 Sch 1 para 10(1)(j) and Sch 6 para 17(1) with Sch 9.
- Scotland: SSI 2012/319 reg 27(1)(j) and SSI 2021/249 reg 57(1)(b)(ix)-(xi).

Pension Credit counts them too (SPC Regs 2002 reg 15(1)), so once the
guarantee credit passport ends, Council Tax Reduction was assessed on less
income than Pension Credit and Housing Benefit.

War pensions and Armed Forces Compensation Scheme payments stay uncounted
where the model cannot see the council's choice: Scotland disregards or omits
them (SSI 2012/319 Sch 3 para 1; SSI 2021/249 reg 57(1)), and English and
Welsh councils may disregard more than the prescribed £10 a week (WSI 2013/3029
reg 34(5); LGFA 1992 Sch 1A para 2(11) and s.13A(1)(c)). Kingston upon Thames
and Newham disregard only £10 a week of each payment, at working age (Kingston
Sch 8 para 20, Newham Sch 8 para 19) and at pension age (each council's Sch 6
para 1), and Kingston limits a working-age family's total to £20 a week (Sch 8
para 40). Westminster's, Merton's and Oxford's working-age schemes disregard
them in full.

Invariants, in 2026, for single people and couples with no children:

1. Differential: Council Tax Reduction and Pension Credit assess the same
   income. For pension-age families under the national pensioner schemes in
   England, Wales and Scotland, with State Pension, private pension, IIDB, IB
   and SDA, no earnings, no pension contributions and savings of at most
   £10,000 (so neither scheme's deemed income from capital applies):
   Council Tax Reduction income is nil where guarantee credit is received
   (SI 2012/2885 Sch 1 para 13 and equivalents), Pension Credit income plus
   the savings credit where the award is savings credit only (para 14), and
   Pension Credit income otherwise.
2. Pound for pound, every scheme: raising IIDB or IB by d, or awarding SDA,
   raises Council Tax Reduction income plus the family's income tax and
   National Insurance by exactly the added amount, wherever the general rules
   apply before and after and the zero floor does not bind. The reduction
   never rises where the route (general rules, savings credit only, guarantee
   credit) is unchanged; in the national schemes, where both awards are
   strictly between nil and the liability, it falls by 20% of the rise in
   income.
3. War pensions: adding war pensions leaves Council Tax Reduction income
   unchanged under the general rules, except in Kingston upon Thames and
   Newham, where it rises by the payments less £10 a week of each (for a
   working-age family in Kingston, less at most £20 a week in all). The
   disregards are written out here from the schemes, not read from the
   parameters.

These compare the model's own measures. Invariant 1 relies on both measures
deducting the family's whole income tax and National Insurance, an existing
approximation in each.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
WEEKS = 52
# 2026-27 weekly rates (SI 2026/148 Sch 1).
IIDB_FULL = 233.90 * WEEKS
LONG_TERM_IB = 146.60 * WEEKS
SDA = (103.85 + 15.50) * WEEKS
WITHDRAWAL_RATE = 0.2
# £10 a week of each war pension; Kingston's £20 a week family limit.
LOCAL_WAR_PENSION_DISREGARD = 10 * WEEKS
KINGSTON_DISREGARD_LIMIT = 20 * WEEKS
PRIVATE_PENSIONS = np.arange(0, 20_001, 1_000)
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Areas of the national pensioner schemes, and of the working-age schemes.
PENSION_AGE_AREAS = {
    "MAIDSTONE": ("ENGLAND", "SOUTH_EAST"),
    "KINGSTON_UPON_THAMES": ("ENGLAND", "LONDON"),
    "NEWHAM": ("ENGLAND", "LONDON"),
    "CARDIFF": ("WALES", "WALES"),
    "GLASGOW_CITY": ("SCOTLAND", "SCOTLAND"),
}
WORKING_AGE_AREAS = {
    "WESTMINSTER": ("ENGLAND", "LONDON"),
    "MERTON": ("ENGLAND", "LONDON"),
    "KINGSTON_UPON_THAMES": ("ENGLAND", "LONDON"),
    "NEWHAM": ("ENGLAND", "LONDON"),
    "OXFORD": ("ENGLAND", "SOUTH_EAST"),
    "CARDIFF": ("WALES", "WALES"),
    "GLASGOW_CITY": ("SCOTLAND", "SCOTLAND"),
}
NATIONAL_SCHEME_AREAS = {"MAIDSTONE", "CARDIFF", "GLASGOW_CITY"}
LOCAL_WAR_PENSION_AREAS = {"KINGSTON_UPON_THAMES", "NEWHAM"}
BENUNIT_VARIABLES = [
    "council_tax_reduction_applicable_income",
    "council_tax_benefit",
    "council_tax_reduction_pensioner",
    "council_tax_reduction_relevant_income_based_benefit",
    "in_receipt_of_guarantee_credit",
    "in_receipt_of_savings_credit_only",
    "pension_credit_income",
    "pension_credit",
]
PERSON_TOTALS = ["income_tax", "national_insurance"]


def money(high):
    return st.floats(0, high, allow_nan=False, allow_infinity=False)


@st.composite
def benefits(draw):
    """IIDB at a 20% to 100% assessment, IB up to the long-term rate, SDA."""
    return dict(
        iidb=draw(st.one_of(st.just(0.0), money(IIDB_FULL))),
        incapacity_benefit=draw(st.one_of(st.just(0.0), money(LONG_TERM_IB))),
        sda=draw(st.booleans()),
    )


@st.composite
def pension_age_family(draw, areas=tuple(PENSION_AGE_AREAS)):
    adults = draw(st.integers(1, 2))
    return dict(
        ages=[draw(st.integers(67, 95)) for _ in range(adults)],
        state_pensions=[draw(money(15_000)) for _ in range(adults)],
        earnings=[0.0] * adults,
        benefits=[draw(benefits()) for _ in range(adults)],
        property_income=draw(st.one_of(st.just(0.0), money(5_000))),
        area=draw(st.sampled_from(areas)),
        council_tax=draw(st.floats(500, 4_000)),
        savings=draw(st.one_of(st.just(0.0), money(10_000))),
        would_claim_pc=draw(st.booleans()),
    )


@st.composite
def working_age_family(draw):
    adults = draw(st.integers(1, 2))
    return dict(
        ages=[draw(st.integers(25, 60)) for _ in range(adults)],
        state_pensions=[0.0] * adults,
        earnings=[draw(st.one_of(st.just(0.0), money(30_000))) for _ in range(adults)],
        benefits=[draw(benefits()) for _ in range(adults)],
        property_income=draw(st.one_of(st.just(0.0), money(5_000))),
        area=draw(st.sampled_from(tuple(WORKING_AGE_AREAS))),
        council_tax=draw(st.floats(500, 4_000)),
        savings=draw(st.one_of(st.just(0.0), money(5_000))),
        would_claim_pc=False,
    )


any_family = st.one_of(pension_age_family(), working_age_family())

# A single pensioner off Pension Credit with every benefit and State Pension
# below the personal allowance, so the general rules apply in every cell.
GENERAL_RULES_PENSIONER = dict(
    ages=[75],
    state_pensions=[9_000.0],
    earnings=[0.0],
    benefits=[dict(iidb=IIDB_FULL * 0.5, incapacity_benefit=LONG_TERM_IB, sda=True)],
    property_income=0.0,
    area="MAIDSTONE",
    council_tax=2_000.0,
    savings=0.0,
    would_claim_pc=False,
)
# A pensioner whose reduction is partial before and after each change, so the
# 20% taper in invariant 2 is checked.
PARTIAL_AWARD_PENSIONER = dict(
    ages=[70],
    state_pensions=[241.30 * WEEKS],
    earnings=[0.0],
    benefits=[dict(iidb=0.0, incapacity_benefit=0.0, sda=False)],
    property_income=0.0,
    area="MAIDSTONE",
    council_tax=2_000.0,
    savings=0.0,
    would_claim_pc=False,
)
# Two adults on the Kingston upon Thames working-age scheme, so the £20 limit
# binds once each has two war pensions.
KINGSTON_COUPLE = dict(
    ages=[40, 40],
    state_pensions=[0.0, 0.0],
    earnings=[8_000.0, 0.0],
    benefits=[dict(iidb=IIDB_FULL * 0.3, incapacity_benefit=0.0, sda=False)] * 2,
    property_income=0.0,
    area="KINGSTON_UPON_THAMES",
    council_tax=2_000.0,
    savings=0.0,
    would_claim_pc=False,
)


def area_of(fam):
    if fam["ages"][0] >= 67:
        return PENSION_AGE_AREAS[fam["area"]]
    return WORKING_AGE_AREAS[fam["area"]]


def situation(variants):
    """One benefit unit and household per (family, private pension, change).

    variants: list of (family, private pension of the first adult, extra
    person inputs for the first adult).
    """
    people, benunits, households = {}, {}, {}
    for i, (fam, private_pension, extra) in enumerate(variants):
        country, region = area_of(fam)
        names = []
        for j, age in enumerate(fam["ages"]):
            name = f"p{i}_{j}"
            b = fam["benefits"][j]
            person = {
                "age": {YEAR: age},
                "state_pension": {YEAR: fam["state_pensions"][j]},
                "employment_income": {YEAR: fam["earnings"][j]},
                "private_pension_income": {YEAR: private_pension * (j == 0)},
                "property_income": {YEAR: fam["property_income"] * (j == 0)},
                "iidb_reported": {YEAR: b["iidb"]},
                "incapacity_benefit_reported": {YEAR: b["incapacity_benefit"]},
                "sda_reported": {YEAR: float(b["sda"])},
            }
            for variable, value in extra.get(j, {}).items():
                person[variable] = {YEAR: value}
            people[name] = person
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_pc": {YEAR: fam["would_claim_pc"]},
            "would_claim_uc": {YEAR: False},
        }
        households[f"h{i}"] = {
            "members": names,
            "country": {YEAR: country},
            "region": {YEAR: region},
            "local_authority": {YEAR: fam["area"]},
            "tenure_type": {YEAR: "OWNED_OUTRIGHT"},
            "council_tax": {YEAR: fam["council_tax"]},
            "savings": {YEAR: fam["savings"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(variants):
    simulation = Simulation(situation=situation(variants))
    values = {v: np.asarray(simulation.calculate(v, YEAR)) for v in BENUNIT_VARIABLES}
    values["tax"] = sum(
        np.asarray(simulation.calculate(v, YEAR, map_to="benunit"))
        for v in PERSON_TOTALS
    )
    values["liability"] = np.asarray(
        simulation.calculate("council_tax_reduction_maximum_eligible_liability", YEAR)
    )
    return values


def route(values):
    """0: general rules; 1: savings credit only; 2: guarantee credit."""
    gc = values["in_receipt_of_guarantee_credit"].astype(bool)
    sc_only = values["in_receipt_of_savings_credit_only"].astype(bool)
    return np.where(gc, 2, np.where(sc_only, 1, 0))


@PROPERTY_SETTINGS
@given(st.lists(pension_age_family(), min_size=1, max_size=4))
@example([GENERAL_RULES_PENSIONER])
def test_council_tax_reduction_and_pension_credit_assess_the_same_income(
    families,
):
    variants = [(fam, p, {}) for fam in families for p in PRIVATE_PENSIONS]
    v = calculate(variants)
    pensioner = v["council_tax_reduction_pensioner"].astype(bool)
    assert np.all(pensioner)
    ctr_income = v["council_tax_reduction_applicable_income"]
    pc_income = v["pension_credit_income"]
    r = route(v)
    expected = np.select(
        [r == 2, r == 1], [0.0, pc_income + v["pension_credit"]], default=pc_income
    )
    assert np.allclose(ctr_income, expected, atol=0.01), [
        (variants[k][0], variants[k][1], ctr_income[k], expected[k], r[k])
        for k in np.flatnonzero(~np.isclose(ctr_income, expected, atol=0.01))[:3]
    ]
    if families == [GENERAL_RULES_PENSIONER]:
        # Not vacuous: the general rules apply and count every benefit.
        assert np.all(r == 0)
        b = GENERAL_RULES_PENSIONER["benefits"][0]
        counted = 9_000 + b["iidb"] + b["incapacity_benefit"] + SDA
        assert np.isclose(ctr_income[0], counted - v["tax"][0], atol=0.01)


CHANGES = {
    "iidb": lambda b: {"iidb_reported": b["iidb"] + 0.2 * IIDB_FULL},
    "incapacity_benefit": lambda b: {
        "incapacity_benefit_reported": b["incapacity_benefit"] + 0.3 * LONG_TERM_IB
    },
    "sda": lambda b: {"sda_reported": 1.0},
}
ADDED = {
    "iidb": lambda b: 0.2 * IIDB_FULL,
    "incapacity_benefit": lambda b: 0.3 * LONG_TERM_IB,
    "sda": lambda b: 0.0 if b["sda"] else SDA,
}


@PROPERTY_SETTINGS
@given(
    st.lists(any_family, min_size=1, max_size=6),
    st.sampled_from(sorted(CHANGES)),
)
@example(
    [GENERAL_RULES_PENSIONER, KINGSTON_COUPLE, PARTIAL_AWARD_PENSIONER],
    "incapacity_benefit",
)
@example([PARTIAL_AWARD_PENSIONER], "iidb")
def test_each_benefit_counts_pound_for_pound_in_every_scheme(families, change):
    variants = []
    for fam in families:
        b = fam["benefits"][0]
        variants.append((fam, 5_000.0, {}))
        variants.append((fam, 5_000.0, {0: CHANGES[change](b)}))
    v = calculate(variants)
    base, plus = slice(0, None, 2), slice(1, None, 2)
    added = np.array([ADDED[change](fam["benefits"][0]) for fam in families])
    income = v["council_tax_reduction_applicable_income"]
    with_tax = income + v["tax"]
    r = route(v)
    passported = v["council_tax_reduction_relevant_income_based_benefit"].astype(bool)
    general = (r[base] == 0) & (r[plus] == 0) & ~passported[base] & ~passported[plus]
    unfloored = general & (income[base] > 0)
    assert np.allclose(
        (with_tax[plus] - with_tax[base])[unfloored], added[unfloored], atol=0.01
    ), (change, [f for f, u in zip(families, unfloored) if u])
    ctr = v["council_tax_benefit"]
    same_route = r[base] == r[plus]
    assert np.all((ctr[plus] <= ctr[base] + 0.01)[same_route]), change
    national = np.array([fam["area"] in NATIONAL_SCHEME_AREAS for fam in families])
    liability = v["liability"]
    partial = (
        general
        & national
        & (ctr[base] > 0.01)
        & (ctr[plus] > 0.01)
        & (ctr[base] < liability[base] - 0.01)
        & (ctr[plus] < liability[plus] - 0.01)
    )
    assert np.allclose(
        (ctr[base] - ctr[plus])[partial],
        (WITHDRAWAL_RATE * (income[plus] - income[base]))[partial],
        atol=0.01,
    ), change
    if PARTIAL_AWARD_PENSIONER in families:
        assert partial[families.index(PARTIAL_AWARD_PENSIONER)]


@st.composite
def war_pensions(draw):
    return {
        "afcs_reported": draw(money(15_000)),
        "war_widows_pension_reported": draw(st.one_of(st.just(0.0), money(8_000))),
    }


def local_war_pension_income(payments, area, pensioner):
    """Counted war pensions under Kingston's or Newham's scheme (Sch 6 para
    1 at pension age; Kingston Sch 8 paras 20 and 40 and Newham Sch 8 para 19
    at working age), from each adult's payments."""
    amounts = [x for person in payments for x in person.values()]
    disregard = sum(min(x, LOCAL_WAR_PENSION_DISREGARD) for x in amounts)
    if area == "KINGSTON_UPON_THAMES" and not pensioner:
        disregard = min(disregard, KINGSTON_DISREGARD_LIMIT)
    return sum(amounts) - disregard


@PROPERTY_SETTINGS
@given(st.data())
def test_war_pensions_count_only_where_the_scheme_says(data):
    # Every draw ends with the Kingston couple, whose four payments meet the
    # £20 a week limit, so the local branch is always exercised.
    families = data.draw(st.lists(any_family, min_size=1, max_size=6))
    families = families + [KINGSTON_COUPLE]
    payments = [[data.draw(war_pensions()) for _ in fam["ages"]] for fam in families]
    payments[-1] = [
        {"afcs_reported": 5_000.0, "war_widows_pension_reported": 3_000.0}
    ] * 2
    variants = []
    for fam, pay in zip(families, payments):
        variants.append((fam, 5_000.0, {}))
        variants.append((fam, 5_000.0, dict(enumerate(pay))))
    v = calculate(variants)
    base, plus = slice(0, None, 2), slice(1, None, 2)
    income = v["council_tax_reduction_applicable_income"]
    r = route(v)
    pensioner = v["council_tax_reduction_pensioner"].astype(bool)
    general = (r[base] == 0) & (r[plus] == 0) & (income[base] > 0)
    expected = np.array(
        [
            local_war_pension_income(pay, fam["area"], pensioner[2 * k])
            if fam["area"] in LOCAL_WAR_PENSION_AREAS
            else 0.0
            for k, (fam, pay) in enumerate(zip(families, payments))
        ]
    )
    rise = income[plus] - income[base]
    assert np.allclose(rise[general], expected[general], atol=0.01), [
        (families[k]["area"], payments[k], rise[k], expected[k])
        for k in np.flatnonzero(general & ~np.isclose(rise, expected, atol=0.01))[:3]
    ]
    # The Kingston couple's four payments meet the £20 a week limit.
    assert np.isclose(rise[-1], 16_000 - KINGSTON_DISREGARD_LIMIT, atol=0.01)

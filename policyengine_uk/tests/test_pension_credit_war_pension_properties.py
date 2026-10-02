"""War pensions and AFCS payments in Pension Credit income.

State Pension Credit Act 2002 s.15(1)(g) counts "a war disablement pension or
war widow's or widower's pension", and the State Pension Credit Regulations
2002 reg 15(5)(aa) count "a guaranteed income payment" of the Armed Forces
Compensation Scheme. Reg 17(7) applies Sch IV, whose para 1 disregards "£10 of
any of the following". `pension_credit_war_pension_income` counts the
claimant's and partner's `afcs` and `war_widows_pension`, each person's less
£10 a week, and Pension Credit income includes it.

Invariants, for single people and couples over State Pension age renting from
the council in 2026, with any mix of AFCS payments and war widow's pensions,
and with a carer receiving Carer's Allowance or Carer Support Payment in some
families (the sources #1952 added):

1. Differential with Housing Benefit. Where Guarantee Credit is not paid and
   neither income floor binds, Housing Benefit applicable income plus its
   income disregard equals Pension Credit income less the counted war pension
   income. The difference is intended: the Housing Benefit (Persons who have
   attained the qualifying age for state pension credit) Regulations 2006 reg
   29(1)(e) and (g) count these payments less £10 (Sch 5 para 1), but the
   Social Security Administration Act 1992 s.134(8) lets an authority modify
   its scheme to disregard "the whole or part" of a prescribed war
   disablement or war widow's pension, and `housing_benefit_applicable_income`
   counts neither `afcs` nor `war_widows_pension`. That is an assumption that
   the authority runs such a local scheme with a full disregard; it is not a
   statement about any particular authority. The draws have no earnings, no
   pension contributions and capital of at most £10,000, so neither tariff
   income nor the earnings rules apply.
2. Bounds and closed form. The counted amount is between 0 and the gross
   payments of the claimant and partner, and equals the sum over the claimant
   and partner of max(0, AFCS + war widow's pension - £520 a year).
3. Monotone. Guarantee Credit does not rise as one person's AFCS payment
   rises, and does not change while the payment is at or below £10 a week.
4. Metamorphic. Moving an amount between `afcs` and `war_widows_pension`
   within one person changes neither Pension Credit income nor Guarantee
   Credit: one £10 a week applies to each person's payments together.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
WEEKS = 52
# Sch IV para 1: £10 a week.
DISREGARD = 10 * WEEKS
PENSIONS = np.arange(0, 20_001, 1_000)
# Weekly AFCS payments for invariant 3, through the disregard and beyond.
AFCS_GRID = np.arange(0, 60.01, 2.5)
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
REGIONS = {
    "ENGLAND": "NORTH_WEST",
    "WALES": "WALES",
    "SCOTLAND": "SCOTLAND",
}


def money(high):
    return st.floats(0, high, allow_nan=False, allow_infinity=False)


def weekly_payment():
    """Annual amount of a weekly payment, often at or near £10 a week."""
    weekly = st.one_of(
        st.just(0.0),
        st.sampled_from([5.0, 9.99, 10.0, 10.01, 25.0, 80.0]),
        money(150),
    )
    return weekly.map(lambda w: w * WEEKS)


@st.composite
def adult(draw):
    return dict(
        age=draw(st.integers(67, 95)),
        state_pension=draw(money(15_000)),
        afcs=draw(weekly_payment()),
        war_widows_pension=draw(weekly_payment()),
        # Share of the person's payments moved to the other source in
        # invariant 4.
        share=draw(st.floats(0, 1)),
    )


@st.composite
def family(draw):
    adults = [draw(adult()) for _ in range(draw(st.integers(1, 2)))]
    return dict(
        adults=adults,
        # A carer in some families, by caring hours or a reported award.
        carer=draw(st.one_of(st.none(), st.integers(0, len(adults) - 1))),
        by_hours=draw(st.booleans()),
        country=draw(st.sampled_from(tuple(REGIONS))),
        rent=draw(money(12_000)),
        council_tax=draw(money(3_000)),
        savings=draw(st.one_of(st.just(0.0), money(10_000))),
        private_pension=draw(money(15_000)),
    )


def person_inputs(fam, j, a, private_pension, afcs, war_widows_pension):
    person = {
        "age": {YEAR: a["age"]},
        "state_pension": {YEAR: a["state_pension"]},
        # All private pension goes to the first adult.
        "private_pension_income": {YEAR: float(private_pension) * (j == 0)},
        "afcs": {YEAR: float(afcs)},
        "war_widows_pension": {YEAR: float(war_widows_pension)},
    }
    if fam["carer"] == j:
        if fam["by_hours"]:
            person["care_hours"] = {YEAR: 35}
        else:
            person["carers_allowance_reported"] = {YEAR: 1}
    return person


def household(fam, names):
    return {
        "members": names,
        "country": {YEAR: fam["country"]},
        "region": {YEAR: REGIONS[fam["country"]]},
        "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
        "rent": {YEAR: fam["rent"]},
        "council_tax": {YEAR: fam["council_tax"]},
        "savings": {YEAR: fam["savings"]},
    }


def simulate(rows):
    """One Simulation with one benefit unit per row.

    Each row is (family, private pension, [(afcs, war widow's pension) per
    adult]). Returns a function giving a benefit-unit array per variable.
    """
    people, benunits, households = {}, {}, {}
    for r, (fam, private_pension, payments) in enumerate(rows):
        names = []
        for j, (a, (afcs, wwp)) in enumerate(zip(fam["adults"], payments)):
            name = f"p{r}_{j}"
            people[name] = person_inputs(fam, j, a, private_pension, afcs, wwp)
            names.append(name)
        benunits[f"b{r}"] = {"members": names}
        households[f"h{r}"] = household(fam, names)
    simulation = Simulation(
        situation={
            "people": people,
            "benunits": benunits,
            "households": households,
        }
    )

    def get(variable):
        return np.asarray(simulation.calculate(variable, YEAR, map_to="benunit"))

    return get


def drawn_payments(fam):
    return [(a["afcs"], a["war_widows_pension"]) for a in fam["adults"]]


def pension_grid(families, payments=drawn_payments):
    """Each family once per private pension on the PENSIONS grid."""
    rows = [(fam, pension, payments(fam)) for fam in families for pension in PENSIONS]
    get = simulate(rows)
    shape = (len(families), len(PENSIONS))
    return lambda variable: get(variable).reshape(shape)


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=4))
def test_pension_credit_and_housing_benefit_differ_only_by_war_pensions(
    families,
):
    get = pension_grid(families)
    gc = get("guarantee_credit")
    hb_income = get("housing_benefit_applicable_income")
    hb_eligible = get("housing_benefit_eligible").astype(bool)
    pc_income = get("pension_credit_income")
    war = get("pension_credit_war_pension_income")
    before_disregard = hb_income + get("housing_benefit_applicable_income_disregard")
    carer_benefit = get("carers_allowance") + get("carer_support_payment")
    for i, fam in enumerate(families):
        if fam["carer"] is not None:
            assert np.all(carer_benefit[i] > 0), fam
        compared = (gc[i] <= 0) & hb_eligible[i] & (hb_income[i] > 0)
        compared &= pc_income[i] > 0
        assert np.allclose(
            before_disregard[i][compared],
            (pc_income[i] - war[i])[compared],
            atol=0.01,
        ), (fam, before_disregard[i][compared], pc_income[i][compared])


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=4))
def test_counted_war_pension_income_bounds_and_closed_form(families):
    get = pension_grid(families)
    war = get("pension_credit_war_pension_income")
    gross = get("afcs") + get("war_widows_pension")
    for i, fam in enumerate(families):
        expected = sum(
            max(0.0, a["afcs"] + a["war_widows_pension"] - DISREGARD)
            for a in fam["adults"]
        )
        assert np.all(war[i] >= 0), fam
        assert np.all(war[i] <= gross[i] + 0.01), fam
        assert np.allclose(war[i], expected, atol=0.01), (fam, war[i], expected)


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=4))
def test_guarantee_credit_does_not_rise_with_an_afcs_payment(families):
    # The first adult's war widow's pension is set to zero so that the grid
    # is the whole of their payments; the partner keeps their drawn payments.
    rows = [
        (
            fam,
            fam["private_pension"],
            [(weekly * WEEKS, 0.0)] + drawn_payments(fam)[1:],
        )
        for fam in families
        for weekly in AFCS_GRID
    ]
    gc = simulate(rows)("guarantee_credit").reshape(len(families), len(AFCS_GRID))
    within_disregard = AFCS_GRID <= 10
    for i, fam in enumerate(families):
        assert np.all(np.diff(gc[i]) <= 0.01), (fam, gc[i])
        assert np.allclose(gc[i][within_disregard], gc[i][0], atol=0.01), (
            fam,
            gc[i],
        )


def moved(fam):
    """Each person's total payments, split between the sources by `share`."""
    return [
        (
            a["share"] * (a["afcs"] + a["war_widows_pension"]),
            (1 - a["share"]) * (a["afcs"] + a["war_widows_pension"]),
        )
        for a in fam["adults"]
    ]


@PROPERTY_SETTINGS
@given(st.lists(family(), min_size=1, max_size=4))
def test_moving_payments_between_sources_within_a_person(families):
    get = pension_grid(families)
    get_moved = pension_grid(families, payments=moved)
    for variable in ["pension_credit_income", "guarantee_credit"]:
        original, after = get(variable), get_moved(variable)
        for i, fam in enumerate(families):
            assert np.allclose(original[i], after[i], atol=0.01), (fam, variable)

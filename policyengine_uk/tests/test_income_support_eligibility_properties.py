"""Income Support eligibility follows only the claimant and partner.

SSCBA 1992 s.124(1) sets each condition for the claimant ("he") and, in
paras (c), (f), (g) and (h), for "the other member of the couple". No new
claim can be made (UC (Transitional Provisions) Regs 2014 reg 6A(1)) and a
partner who takes over an award does so by claiming (Claims and Payments
Regs 1987 reg 4(4)), so the claimant is the partner with the existing award.
Nobody else in a benefit unit is named, so:

- adding a member who is neither the claimant, the partner nor a child or
  young person in the family (an adult outside the family, or a child placed
  by a local authority, IS reg 16(4)) never changes income_support_eligible,
  whatever that member's age, ESA, JSA, Income Support, caring or work;
- income_support_eligible equals a family-by-family reading of the model's
  gate: one of the claimant and partner reports Income Support, is under
  state pension age, is a carer (or a lone parent of a child aged 5 or under,
  the model's reading of Sch 1B para 1), has no contributory ESA or JSA, is
  not a non-carer working 16 hours a week or more, and has no other member
  of the couple who is a non-carer working 24 hours or more (s.124(1)(aa),
  (c), (e), (f), (h); IS Regs 1987 regs 5(1), 5(1A) and 6(4)(c)); neither
  has income-related ESA or income-based JSA (s.124(1)(h), (f)), meaning the
  award on their reported amounts after that benefit's capital test, or an
  esa_income or jsa_income entered directly; and capital is within the
  Income Support limit;
- raising any claimant's or partner's hours or JSA never makes a family
  eligible, because (c) and (f) only ever bar a claim.

The second property is a reference check of the bounded model gate, not of
legal entitlement: caring, work hours, ESA, JSA and Income Support are the
model's reported or proxy inputs, it reads state pension age from the model
(is_SP_age), and the means test is out of scope.

Roles are given explicitly (is_claimant_or_partner), so the properties test
the eligibility rule rather than the role inference; the inferred case is
covered in income_support_claimant_partner_gates.yaml. Each example builds
many families in one simulation, in separate households and benefit units.
Capital is either entered as each benefit unit's assessable capital or as
household savings, which all three capital tests read.
"""

import math

import numpy as np
from hypothesis import HealthCheck, event, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2025


@st.composite
def adult_inputs(draw, min_age=18):
    inputs = {
        "age": draw(st.integers(min_age, 90)),
        "receives_carer_benefit": draw(st.booleans()),
        "care_hours": draw(st.sampled_from([0, 34, 35])),
        "esa_income_reported": draw(st.sampled_from([0, 0, 200, 3_000])),
        "esa_contrib_reported": draw(st.sampled_from([0, 0, 3_000])),
        "income_support_reported": draw(st.sampled_from([0, 1_000, 1_000])),
        # 0, 15, 16, 20, 24 and 40 hours a week.
        "hours_worked": draw(st.sampled_from([0, 0, 780, 832, 1_040, 1_248, 2_080])),
        "jsa_contrib_reported": draw(st.sampled_from([0, 0, 0, 3_000])),
        "jsa_income_reported": draw(st.sampled_from([0, 0, 0, 200, 3_000])),
    }
    if draw(st.integers(0, 2)) == 0:
        # A typical award holder: a working-age carer with Income Support and
        # no other benefit or paid work. Without these, the conditions
        # together leave few families eligible, and each must be tested from
        # both sides.
        inputs.update(
            age=draw(st.integers(min_age, max(min_age, 60))),
            receives_carer_benefit=True,
            income_support_reported=1_000,
            esa_income_reported=0,
            esa_contrib_reported=0,
            hours_worked=draw(st.sampled_from([0, 780])),
            jsa_contrib_reported=0,
            jsa_income_reported=0,
        )
    return inputs


PRIMED_CLAIMANT = {
    "income_support_reported": 1_000,
    "esa_income_reported": 0,
    "esa_contrib_reported": 0,
    "hours_worked": 0,
    "jsa_contrib_reported": 0,
    "jsa_income_reported": 0,
}


@st.composite
def families(draw):
    """A claimant, an optional partner, up to three dependants and capital.

    Half the families are drawn at random. The rest are primed to sit at the
    edge of eligibility, where an added member could change the result: a
    claimant who reports Income Support and cares, or a lone parent who
    reports it, does not care and has only children over 5.
    """
    shape = draw(st.sampled_from(["random", "random", "carer", "lone_parent"]))
    n_dependants = draw(st.integers(1 if shape == "lone_parent" else 0, 3))
    dependants = []
    for _ in range(n_dependants):
        if shape == "lone_parent":
            dependant = {"age": draw(st.integers(6, 15))}
        elif draw(st.booleans()):
            dependant = {"age": draw(st.integers(0, 15))}
        else:
            # A qualifying young person: 16-19 in non-advanced education.
            dependant = {
                "age": draw(st.integers(16, 19)),
                "current_education": "UPPER_SECONDARY",
            }
        dependants.append(dependant)
    eldest_dependant = max([d["age"] for d in dependants], default=0)
    adults = [draw(adult_inputs(min_age=max(18, eldest_dependant + 16)))]
    if shape != "lone_parent" and draw(st.booleans()):
        adults.append(draw(adult_inputs()))
    if shape == "carer":
        adults[0].update(
            PRIMED_CLAIMANT, age=min(adults[0]["age"], 65), receives_carer_benefit=True
        )
    elif shape == "lone_parent":
        adults[0].update(
            PRIMED_CLAIMANT,
            age=min(adults[0]["age"], 65),
            receives_carer_benefit=False,
            care_hours=0,
        )
    for adult in adults:
        adult["is_parent"] = n_dependants > 0
    capital = draw(st.sampled_from([0, 6_250, 10_000, 20_000]))
    return adults, dependants, capital


@st.composite
def excluded_members(draw):
    """A member who is neither claimant, partner nor in the family.

    Either an adult not in education (so a 16 to 19 year old is not a
    qualifying young person), or a child placed by a local authority.
    """
    if draw(st.booleans()):
        # Mostly 5 or under, the ages that could open the lone-parent route.
        return {
            "age": draw(st.one_of(st.integers(0, 5), st.integers(6, 15))),
            "is_looked_after_by_local_authority": True,
            "receives_carer_benefit": draw(st.booleans()),
        }
    return {
        **draw(adult_inputs(min_age=16)),
        "current_education": "NOT_IN_EDUCATION",
    }


@st.composite
def direct_award(draw, n):
    """An award entered directly for each of n families (half the time), or None."""
    if draw(st.booleans()):
        return draw(st.lists(st.sampled_from([0, 3_000]), min_size=n, max_size=n))
    return None


@st.composite
def input_settings(draw, n):
    """How capital, income-related ESA and income-based JSA are entered.

    Capital goes in as assessable capital or as household savings. When
    esa_income or jsa_income is entered directly, it is entered for every
    family, so it is a simulation input and the formula does not run.
    """
    capital_as_savings = draw(st.booleans())
    return capital_as_savings, draw(direct_award(n)), draw(direct_award(n))


def label(units, capital_as_savings, esa_income, jsa_income):
    """Record which input surfaces an example reaches (--hypothesis-show-statistics)."""
    event(
        "capital as household savings" if capital_as_savings else "assessable capital"
    )
    event("esa_income entered directly" if esa_income else "esa_income calculated")
    event("jsa_income entered directly" if jsa_income else "jsa_income calculated")
    adults = [a for family_adults, *_ in units for a in family_adults]
    if any(a["hours_worked"] >= 832 for a in adults):
        event("claimant or partner works 16 hours or more")
    if any(a["jsa_contrib_reported"] or a["jsa_income_reported"] for a in adults):
        event("claimant or partner reports JSA")
    extras = [extra for *_, extra in units if extra is not None]
    if any(e.get("is_looked_after_by_local_authority") for e in extras):
        event("placed child added")
    if any(
        e.get("income_support_reported") or e.get("esa_income_reported") for e in extras
    ):
        event("added member reports IS or ESA")
    if any(e.get("hours_worked") or e.get("jsa_income_reported") for e in extras):
        event("added member works or reports income-based JSA")


def situation(units, capital_as_savings, esa_income, jsa_income):
    label(units, capital_as_savings, esa_income, jsa_income)
    people, benunits, households = {}, {}, {}
    for i, (adults, dependants, capital, extra) in enumerate(units):
        members = [(m, True) for m in adults] + [(m, False) for m in dependants]
        if extra is not None:
            members.append((extra, False))
        names = []
        for j, (inputs, claimant_or_partner) in enumerate(members):
            name = f"p{i}_{j}"
            people[name] = {k: {YEAR: v} for k, v in inputs.items()}
            people[name]["is_claimant_or_partner"] = {YEAR: claimant_or_partner}
            names.append(name)
        benunits[f"b{i}"] = {"members": names}
        households[f"h{i}"] = {"members": names}
        if capital_as_savings:
            households[f"h{i}"]["savings"] = {YEAR: capital}
        else:
            benunits[f"b{i}"]["income_support_assessable_capital"] = {YEAR: capital}
            benunits[f"b{i}"]["esa_income_assessable_capital"] = {YEAR: capital}
            benunits[f"b{i}"]["jsa_income_assessable_capital"] = {YEAR: capital}
        if esa_income is not None:
            benunits[f"b{i}"]["esa_income"] = {YEAR: esa_income[i % len(esa_income)]}
        if jsa_income is not None:
            benunits[f"b{i}"]["jsa_income"] = {YEAR: jsa_income[i % len(jsa_income)]}
    return {"people": people, "benunits": benunits, "households": households}


SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

# The invariance property needs rarer combinations (a placed young child in a
# lone parent's family, a direct esa_income beside an added member's ESA), so
# it runs more examples.
INVARIANCE_SETTINGS = settings(SETTINGS, max_examples=25)

FAMILIES = st.lists(st.tuples(families(), excluded_members()), min_size=1, max_size=8)


@INVARIANCE_SETTINGS
@given(FAMILIES, st.data())
def test_excluded_member_never_changes_is_eligibility(drawn, data):
    capital_as_savings, esa_income, jsa_income = data.draw(input_settings(len(drawn)))
    without = [(*family, None) for family, _ in drawn]
    with_extra = [(*family, extra) for family, extra in drawn]
    sim = Simulation(
        situation=situation(
            without + with_extra, capital_as_savings, esa_income, jsa_income
        )
    )
    eligible = sim.calculate("income_support_eligible", YEAR)
    if eligible.any():
        event("some family eligible")
    flags = sim.calculate("is_claimant_or_partner", YEAR)
    dependant = sim.calculate("is_child_or_young_person_for_legacy_benefits", YEAR)
    sizes = [len(a) + len(d) + (e is not None) for a, d, _, e in without + with_extra]
    ends = np.cumsum(sizes)
    k = len(drawn)
    for i in range(k):
        # The added member is the last of its benefit unit: neither claimant,
        # partner nor in the family.
        last = ends[k + i] - 1
        assert not flags[last] and not dependant[last], drawn[i]
        assert eligible[i] == eligible[k + i], drawn[i]


def tariff_income(capital, rules):
    """Annual tariff income: £1 a week for each £250 (or part) over £6,000."""
    excess = max(0, capital - rules.tariff_income.threshold)
    return (
        math.ceil(excess / rules.tariff_income.step) * rules.tariff_income.amount * 52
    )


def income_related_award(reported, capital, rules):
    """Whether a reported award survives a legacy benefit's capital test."""
    return (
        reported > 0
        and capital <= rules.limit
        and reported > tariff_income(capital, rules)
    )


def reference_eligibility(
    adults, dependants, capital, esa_income, jsa_income, sp_age, parameters
):
    """The model's Income Support gate, read family by family."""
    IS = parameters.gov.dwp.income_support
    WORK = IS.eligibility.remunerative_work
    JSA = parameters.gov.dwp.JSA.income
    child_ages = [d["age"] for d in dependants if d["age"] < 16]
    lone_parent_with_young_child = (
        len(adults) == 1
        and len(dependants) > 0
        and min(child_ages, default=math.inf)
        <= IS.eligibility.lone_parent_youngest_child_age_limit
    )

    def carer(adult):
        return adult["receives_carer_benefit"] or adult["care_hours"] >= 35

    def works(adult, threshold):
        # IS Regs 1987 reg 5(1) and (1A); reg 6(4)(c) for a carer.
        return not carer(adult) and adult["hours_worked"] / 52 >= threshold

    def is_claimant(i):
        adult, others = adults[i], adults[:i] + adults[i + 1 :]
        return (
            adult["income_support_reported"] > 0
            and (carer(adult) or lone_parent_with_young_child)
            and not sp_age[i]
            and adult["esa_contrib_reported"] == 0
            and adult["jsa_contrib_reported"] == 0
            and not works(adult, WORK.claimant_hours)
            and not any(works(other, WORK.partner_hours) for other in others)
        )

    if esa_income is not None:
        income_related_esa = esa_income > 0
    else:
        income_related_esa = income_related_award(
            sum(a["esa_income_reported"] for a in adults),
            capital,
            parameters.gov.dwp.ESA.income.capital,
        )
    if jsa_income is not None:
        income_based_jsa = jsa_income > 0
    else:
        income_based_jsa = JSA.active and income_related_award(
            sum(a["jsa_income_reported"] for a in adults), capital, JSA.capital
        )
    return (
        any(is_claimant(i) for i in range(len(adults)))
        and not income_related_esa
        and not income_based_jsa
        and capital <= IS.means_test.capital.limit
    )


@SETTINGS
@given(FAMILIES, st.data())
def test_is_eligibility_matches_a_family_by_family_reading(drawn, data):
    capital_as_savings, esa_income, jsa_income = data.draw(input_settings(len(drawn)))
    units = [(*family, extra) for family, extra in drawn]
    sim = Simulation(
        situation=situation(units, capital_as_savings, esa_income, jsa_income)
    )
    eligible = sim.calculate("income_support_eligible", YEAR)
    if eligible.any():
        event("some family eligible")
    sp_age = sim.calculate("is_SP_age", YEAR)
    parameters = sim.tax_benefit_system.parameters(YEAR)
    start = 0
    for i, (adults, dependants, capital, extra) in enumerate(units):
        expected = reference_eligibility(
            adults,
            dependants,
            capital,
            None if esa_income is None else esa_income[i],
            None if jsa_income is None else jsa_income[i],
            sp_age[start : start + len(adults)],
            parameters,
        )
        assert eligible[i] == expected, units[i]
        start += len(adults) + len(dependants) + 1


@st.composite
def more_work_or_jsa(draw, adults):
    """The same adults with more paid work or JSA (s.124(1)(c), (f))."""
    more = [dict(adult) for adult in adults]
    for adult in more:
        adult["hours_worked"] += draw(st.sampled_from([0, 260, 832, 1_248]))
        adult["jsa_contrib_reported"] += draw(st.sampled_from([0, 0, 3_000]))
        adult["jsa_income_reported"] += draw(st.sampled_from([0, 0, 3_000]))
    return more


@SETTINGS
@given(st.lists(families(), min_size=1, max_size=8), st.data())
def test_more_work_or_jsa_never_makes_a_family_eligible(drawn, data):
    """(c) and (f) only ever bar a claim: raising any claimant's or partner's
    hours or JSA cannot turn an ineligible family eligible."""
    capital_as_savings, esa_income, jsa_income = data.draw(input_settings(len(drawn)))
    jsa_income = None if jsa_income is None else jsa_income * 2
    more = [
        (data.draw(more_work_or_jsa(adults)), dependants, capital)
        for adults, dependants, capital in drawn
    ]
    units = [(*family, None) for family in drawn + more]
    sim = Simulation(
        situation=situation(
            units,
            capital_as_savings,
            None if esa_income is None else esa_income * 2,
            jsa_income,
        )
    )
    eligible = sim.calculate("income_support_eligible", YEAR)
    if eligible[: len(drawn)].any():
        event("some family eligible before")
    if (eligible[: len(drawn)] & ~eligible[len(drawn) :]).any():
        event("more work or JSA removed eligibility")
    for i in range(len(drawn)):
        assert not (eligible[len(drawn) + i] and not eligible[i]), (drawn[i], more[i])

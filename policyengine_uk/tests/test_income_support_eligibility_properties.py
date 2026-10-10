"""Income Support eligibility follows only the claimant and partner.

SSCBA 1992 s.124(1) sets each condition for the claimant ("he") and, in
paras (c), (f), (g) and (h), for "the other member of the couple". No new
claim can be made (UC (Transitional Provisions) Regs 2014 reg 6A(1)) and a
partner who takes over an award does so by claiming (Claims and Payments
Regs 1987 reg 4(4)), so the claimant is the partner with the existing award.
No adult outside the couple is named, so:

- adding an adult who is neither the claimant, the partner nor a young person
  in the family never changes income_support_eligible, whatever that adult's
  age, ESA, JSA, Income Support, caring or work;
- income_support_eligible equals a family-by-family reading of the model's
  gate: one of the claimant and partner reports Income Support, is under
  the qualifying age for State Pension Credit, is in a prescribed category
  the model covers (a carer; a lone parent of a child aged 5 or under, the
  model's reading of Sch 1B para 1, counting only children in the
  household, reg 16(4); or a single claimant with a child placed by a local
  authority, para 2), has no contributory ESA or JSA, is not a non-carer
  working 16 hours a week or more, and has no other member of the couple who
  is a non-carer working 24 hours or more (s.124(1)(aa), (c), (e), (f), (h);
  IS Regs 1987 regs 5(1), 5(1A) and 6(4)(c)); neither has income-related ESA
  or income-based JSA (s.124(1)(h), (f)), meaning the award on their reported
  amounts after that benefit's capital and remunerative work tests
  (legacy_award_work_reference), or an esa_income or jsa_income the reported
  amounts do not explain (one that equals neither the award on everyone's
  reported amounts nor their plain total); the couple is not taken to be on
  State Pension Credit (s.124(1)(g)); and capital is within the Income
  Support limit;
- raising any claimant's or partner's hours or JSA never makes a family
  eligible. (c) and (f) only ever bar a claim, except where the work ends an
  income-related ESA or income-based JSA award that barred it: a carer is
  not in remunerative work for Income Support (reg 6(4)(c)) but is for JSA,
  so a carer's own JSA award ends at 16 hours. The one other path is (g):
  income-based JSA reported by the claimant or partner can end the Housing
  Benefit route to the inferred SI 2019/37 saving
  (has_mixed_age_couple_pension_credit_saving) when neither member reports
  Pension Credit, which can take a mixed-age couple out of the Pension
  Credit age conditions and so lift the (g) bar. That Housing Benefit route
  already fails when either of them reports Income Support, and a couple in
  which neither does has no award holder, so it is never eligible.

The first and third hold for every input except at the value convention's
boundary. A stored esa_income or jsa_income (entered directly or replaced by
a reform) that equals what the reported amounts give, to within half a penny
after rounding to the precision it is stored in, is read through them. So a
change to another member's report, or to the claimant's own, can change how
that award is read.
The generators stay off that boundary. They enter £4,000, which no generated
total of reports can equal, or £0, whose two readings agree: where £0 is
what the reports give, they give no award to bar the claim either.
test_income_support_direct_inputs.py (JSA) and
test_income_support_esa_entered_directly.py (ESA) test the boundary by
example, with the intended results.

The second property is a reference check of the bounded model gate, not of
legal entitlement: caring, work hours, ESA, JSA and Income Support are the
model's reported or proxy inputs; it reads the qualifying age
(has_attained_state_pension_credit_qualifying_age) and the model's proxy for
being on Pension Credit (meets_pension_credit_age_conditions and
would_claim_pc) from the model; and the means test is out of scope. No
claimant or partner drawn here reports Pension Credit or Housing Benefit
(only some added adults do), so in 2025 no family with a claimant or partner
under the qualifying age meets the Pension Credit age conditions. The
differential asserts this, and income_support_claimant_partner_gates.yaml
pins (g).

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

from legacy_award_work_reference import esa_screen, jsa_screen
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

    Some families are drawn at random. The rest are primed to sit at the
    edge of eligibility:

    - carer: a claimant who reports Income Support and cares;
    - lone_parent: a lone parent who reports it, does not care and has only
      children over 5;
    - split_couple: one partner reports Income Support but fails a
      condition, and the other qualifies but has no award, so the carer
      cannot take the award over.

    A quarter of families also have a child placed by a local authority.
    """
    shape = draw(
        st.sampled_from(["random", "random", "carer", "lone_parent", "split_couple"])
    )
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
    if shape == "split_couple" or (shape != "lone_parent" and draw(st.booleans())):
        adults.append(draw(adult_inputs()))
    if shape == "split_couple":
        failure = draw(st.sampled_from(["over_qualifying_age", "no_category", "esa"]))
        adults[0].update(
            PRIMED_CLAIMANT,
            age=draw(st.integers(max(adults[0]["age"], 66), 90))
            if failure == "over_qualifying_age"
            else min(adults[0]["age"], 65),
            receives_carer_benefit=failure != "no_category",
            care_hours=0,
            esa_contrib_reported=3_000 if failure == "esa" else 0,
        )
        adults[1].update(
            age=min(adults[1]["age"], 65),
            receives_carer_benefit=True,
            income_support_reported=0,
            esa_income_reported=0,
            esa_contrib_reported=0,
        )
    elif shape == "carer":
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
    if draw(st.integers(0, 3)) == 0:
        dependants.append(
            {
                # Up to 17: para 2 covers only a placed child under 16.
                "age": draw(st.integers(0, 17)),
                "is_looked_after_by_local_authority": True,
            }
        )
    for adult in adults:
        adult["is_parent"] = n_dependants > 0
    capital = draw(st.sampled_from([0, 6_250, 10_000, 20_000]))
    return adults, dependants, capital


@st.composite
def excluded_members(draw):
    """An adult who is neither claimant, partner nor in the family.

    They are not in education, so a 16 to 19 year old is not a qualifying
    young person. Most are primed with what barred or opened the claim when
    every member counted: over state pension age, income-related ESA, an
    Income Support report, or caring. Some are primed with what the
    s.124(1)(g) proxy reads for a couple: over the qualifying age, with
    reported Pension Credit or Housing Benefit.
    """
    adult = {
        **draw(adult_inputs(min_age=16)),
        "current_education": "NOT_IN_EDUCATION",
    }
    primed = draw(
        st.sampled_from(["random", "elderly", "esa", "award", "carer", "pension"])
    )
    if primed == "elderly":
        adult["age"] = draw(st.integers(66, 90))
    elif primed == "esa":
        adult["esa_income_reported"] = 3_000
    elif primed == "award":
        adult["income_support_reported"] = 1_000
    elif primed == "carer":
        adult["receives_carer_benefit"] = True
    elif primed == "pension":
        adult["age"] = draw(st.integers(66, 90))
        reported = draw(
            st.sampled_from(["pension_credit_reported", "housing_benefit_reported"])
        )
        adult[reported] = 1_000
    return adult


@st.composite
def direct_award(draw, n):
    """An award entered directly for each of n families (half the time), or None.

    £4,000 is neither a total of the reported amounts drawn here nor such a
    total less tariff income, so it is always read as entered directly.
    """
    if draw(st.booleans()):
        return draw(
            st.lists(st.sampled_from([0, 4_000, 4_000]), min_size=n, max_size=n)
        )
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
    if any(
        d.get("is_looked_after_by_local_authority")
        for _, dependants, *_ in units
        for d in dependants
    ):
        event("family with a placed child")
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
# The differential property needs a directly entered award to meet an otherwise
# eligible family, so it runs as many.
DIFFERENTIAL_SETTINGS = settings(SETTINGS, max_examples=25)

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
    adults,
    dependants,
    capital,
    esa_income,
    jsa_income,
    attained_qualifying_age,
    on_pension_credit,
    parameters,
):
    """The model's Income Support gate, read family by family."""
    IS = parameters.gov.dwp.income_support
    WORK = IS.eligibility.remunerative_work
    JSA = parameters.gov.dwp.JSA.income
    # A child placed by a local authority is not a member of the household
    # (reg 16(4)), so not a child for para 1, but brings a single claimant
    # within para 2.
    placed = [d for d in dependants if d.get("is_looked_after_by_local_authority")]
    in_household = [d for d in dependants if d not in placed]
    child_ages = [d["age"] for d in in_household if d["age"] < 16]
    lone_parent_with_young_child = (
        len(adults) == 1
        and len(in_household) > 0
        and min(child_ages, default=math.inf)
        <= IS.eligibility.lone_parent_youngest_child_age_limit
    )
    # A child is under 16 (SSCBA s.137(1)).
    single_with_placed_child = len(adults) == 1 and any(d["age"] < 16 for d in placed)

    def carer(adult):
        return adult["receives_carer_benefit"] or adult["care_hours"] >= 35

    def works(adult, threshold):
        # IS Regs 1987 reg 5(1) and (1A); reg 6(4)(c) for a carer.
        return not carer(adult) and adult["hours_worked"] / 52 >= threshold

    def is_claimant(i):
        adult, others = adults[i], adults[:i] + adults[i + 1 :]
        return (
            adult["income_support_reported"] > 0
            and (
                carer(adult) or lone_parent_with_young_child or single_with_placed_child
            )
            and not attained_qualifying_age[i]
            and adult["esa_contrib_reported"] == 0
            and adult["jsa_contrib_reported"] == 0
            and not works(adult, WORK.claimant_hours)
            and not any(works(other, WORK.partner_hours) for other in others)
        )

    # The awards on the claimant's and partner's reports, after the capital
    # and remunerative work tests. Members outside the family are not
    # candidates when either of them reports one.
    if esa_income is not None:
        # Within half a penny of zero is no award.
        income_related_esa = esa_income > 0.005
    else:
        income_related_esa = income_related_award(
            sum(a["esa_income_reported"] for a in adults),
            capital,
            parameters.gov.dwp.ESA.income.capital,
        ) and esa_screen(adults, [], capital, parameters)
    if jsa_income is not None:
        # Within half a penny of zero is no award.
        income_based_jsa = jsa_income > 0.005
    else:
        income_based_jsa = (
            JSA.active
            and income_related_award(
                sum(a["jsa_income_reported"] for a in adults), capital, JSA.capital
            )
            and jsa_screen(adults, [], capital, parameters)
        )
    return (
        any(is_claimant(i) for i in range(len(adults)))
        and not income_related_esa
        and not income_based_jsa
        # s.124(1)(g), read through the model's proxy for being on Pension
        # Credit.
        and not on_pension_credit
        and capital <= IS.means_test.capital.limit
    )


def explained_by_reports(
    esa_income, reported_total, capital, parameters, rules=None, screen=True
):
    """Whether an esa_income (or, with the JSA capital rules, a jsa_income)
    equals what the reported amounts give: the award after the capital and
    remunerative work tests (screen: whether the reports pass the work test),
    or their plain total. Income-based JSA is active in YEAR."""
    ESA = rules if rules is not None else parameters.gov.dwp.ESA.income.capital
    tariff = (
        math.ceil(
            max(0, capital - ESA.tariff_income.threshold) / ESA.tariff_income.step
        )
        * ESA.tariff_income.amount
        * 52
    )
    award = (
        max(0, reported_total - tariff)
        if reported_total > 0 and capital <= ESA.limit and screen
        else 0
    )
    return abs(esa_income - award) <= 0.005 or abs(esa_income - reported_total) <= 0.005


@DIFFERENTIAL_SETTINGS
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
    attained_qualifying_age = sim.calculate(
        "has_attained_state_pension_credit_qualifying_age", YEAR
    )
    on_pension_credit = sim.calculate(
        "meets_pension_credit_age_conditions", YEAR
    ) & sim.calculate("would_claim_pc", YEAR)
    parameters = sim.tax_benefit_system.parameters(YEAR)
    start = 0
    for i, (adults, dependants, capital, extra) in enumerate(units):
        # An esa_income or jsa_income the reported amounts explain is read
        # through them, like a calculated one.
        entered_esa = entered_jsa = None
        # The award on everyone's reports, which the value rule compares
        # with, applies the work tests to the whole benefit unit.
        others = [extra] if extra is not None else []
        if esa_income is not None:
            reported_total = sum(
                member.get("esa_income_reported", 0) for member in adults + [extra]
            )
            if not explained_by_reports(
                esa_income[i],
                reported_total,
                capital,
                parameters,
                screen=esa_screen(adults, others, capital, parameters),
            ):
                entered_esa = esa_income[i]
        if jsa_income is not None:
            reported_total = sum(
                member.get("jsa_income_reported", 0) for member in adults + [extra]
            )
            if not explained_by_reports(
                jsa_income[i],
                reported_total,
                capital,
                parameters,
                parameters.gov.dwp.JSA.income.capital,
                screen=jsa_screen(adults, others, capital, parameters),
            ):
                entered_jsa = jsa_income[i]
        expected = reference_eligibility(
            adults,
            dependants,
            capital,
            entered_esa,
            entered_jsa,
            attained_qualifying_age[start : start + len(adults)],
            on_pension_credit[i],
            parameters,
        )
        assert eligible[i] == expected, units[i]
        # The docstring's claim: no family drawn here with a claimant or
        # partner under the qualifying age is taken to be on Pension Credit.
        assert (
            not on_pension_credit[i]
            or attained_qualifying_age[start : start + len(adults)].all()
        ), units[i]
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
    hours or JSA cannot turn an ineligible family eligible, unless the work
    ends an income-related ESA or income-based JSA award that barred it. More
    JSA can lift the (g) bar only for a couple with no Income Support report,
    which is never eligible (see the module docstring)."""
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
    n = len(drawn)
    # An award entered directly is the same on both sides. One calculated
    # from reports can end when the work test fails: these families have no
    # member outside the couple, so esa_income and jsa_income are the
    # claimant's and partner's award, after tariff income and while the
    # scheme is active.
    lost_award = np.zeros(n, dtype=bool)
    for variable, direct in [("esa_income", esa_income), ("jsa_income", jsa_income)]:
        if direct is None:
            award = sim.calculate(variable, YEAR)
            lost_award |= (award[:n] > 0) & (award[n:] <= 0)
    if (eligible[n:] & ~eligible[:n] & lost_award).any():
        event("more work ended an award that barred Income Support")
    for i in range(n):
        assert lost_award[i] or not (eligible[n + i] and not eligible[i]), (
            drawn[i],
            more[i],
        )


# One fixed example: situation() records Hypothesis events, so it runs inside
# a test with a single, constant draw.
@settings(max_examples=1, deadline=None, derandomize=True)
@given(st.just(None))
def test_direct_awards_match_the_reference_deterministically(_):
    """Both direct-award modes, for an otherwise eligible carer: a direct
    income-related ESA or income-based JSA of £4,000, which no report
    explains, bars the claim; a direct £0 lifts a reported award's bar.
    Random draws reach these combinations only some of the time."""
    carer = {
        "age": 40,
        "receives_carer_benefit": True,
        "care_hours": 0,
        "esa_income_reported": 0,
        "esa_contrib_reported": 0,
        "income_support_reported": 1_000,
        "hours_worked": 0,
        "jsa_contrib_reported": 0,
        "jsa_income_reported": 0,
    }
    reporting_carer = {
        **carer,
        "esa_income_reported": 3_000,
        "jsa_income_reported": 3_000,
    }
    cases = [
        (carer, 4_000, 0, False),
        (carer, 0, 4_000, False),
        (carer, 0, 0, True),
        (reporting_carer, 0, 0, True),
        (reporting_carer, 4_000, 0, False),
    ]
    units = [([dict(adult)], [], 0, None) for adult, *_ in cases]
    sim = Simulation(
        situation=situation(units, False, [c[1] for c in cases], [c[2] for c in cases])
    )
    eligible = sim.calculate("income_support_eligible", YEAR)
    parameters = sim.tax_benefit_system.parameters(YEAR)
    for i, (adult, esa, jsa, expected) in enumerate(cases):
        reference = reference_eligibility(
            [adult], [], 0, esa, jsa, [False], False, parameters
        )
        assert reference == expected, (adult, esa, jsa)
        assert eligible[i] == expected, (adult, esa, jsa)

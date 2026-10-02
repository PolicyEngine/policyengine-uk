"""Income Support eligibility follows only the claimant and partner.

SSCBA 1992 s.124(1) sets each condition for the claimant ("he") and, in
paras (c), (f), (g) and (h), for "the other member of the couple". No new
claim can be made (UC (Transitional Provisions) Regs 2014 reg 6A(1)) and a
partner who takes over an award does so by claiming (Claims and Payments
Regs 1987 reg 4(4)), so the claimant is the partner with the existing award.
No adult outside the couple is named, so:

- adding an adult who is neither the claimant, the partner nor a young person
  in the family never changes income_support_eligible, whatever that adult's
  age, ESA, Income Support or caring. The declared exception, outside the
  values drawn here, is an esa_income entered directly that the new adult's
  report makes equal to what the reports give: it is then read through the
  reports (test_income_support_esa_entered_directly.py);
- income_support_eligible equals a family-by-family reading of the model's
  gate: one of the claimant and partner reports Income Support, is under
  state pension age, is in a prescribed category the model covers (a carer;
  a lone parent of a child aged 5 or under, the model's reading of Sch 1B
  para 1, counting only children in the household, reg 16(4); or a single
  claimant with a child placed by a local authority, para 2) and has no
  contributory ESA
  (s.124(1)(aa), (e), (h)); neither has income-related ESA (s.124(1)(h)),
  meaning the award on their reported amounts after the ESA capital test, or
  an esa_income the reported amounts do not explain (one that equals neither
  the award on everyone's reported amounts nor their plain total); and
  capital is within the Income Support limit.

The second property is a reference check of the bounded model gate, not of
legal entitlement: caring, ESA and Income Support are the model's reported
or proxy inputs, it reads state pension age from the model (is_SP_age), and
the means test is out of scope.

Roles are given explicitly (is_claimant_or_partner), so the properties test
the eligibility rule rather than the role inference; the inferred case is
covered in income_support_claimant_partner_gates.yaml. Each example builds
many families in one simulation, in separate households and benefit units.
Capital is either entered as each benefit unit's assessable capital or as
household savings, which both capital tests read.
"""

import math

import numpy as np
from hypothesis import HealthCheck, event, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2025


@st.composite
def adult_inputs(draw, min_age=18):
    return {
        "age": draw(st.integers(min_age, 90)),
        "receives_carer_benefit": draw(st.booleans()),
        "care_hours": draw(st.sampled_from([0, 34, 35])),
        "esa_income_reported": draw(st.sampled_from([0, 0, 200, 3_000])),
        "esa_contrib_reported": draw(st.sampled_from([0, 0, 3_000])),
        "income_support_reported": draw(st.sampled_from([0, 1_000, 1_000])),
    }


PRIMED_CLAIMANT = {
    "income_support_reported": 1_000,
    "esa_income_reported": 0,
    "esa_contrib_reported": 0,
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
                "age": draw(st.integers(0, 15)),
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
    Income Support report, or caring.
    """
    adult = {
        **draw(adult_inputs(min_age=16)),
        "current_education": "NOT_IN_EDUCATION",
    }
    primed = draw(st.sampled_from(["random", "elderly", "esa", "award", "carer"]))
    if primed == "elderly":
        adult["age"] = draw(st.integers(66, 90))
    elif primed == "esa":
        adult["esa_income_reported"] = 3_000
    elif primed == "award":
        adult["income_support_reported"] = 1_000
    elif primed == "carer":
        adult["receives_carer_benefit"] = True
    return adult


@st.composite
def input_settings(draw, n):
    """How capital and income-related ESA are entered for n families.

    Capital goes in as assessable capital or as household savings. When
    esa_income is entered directly, it is entered for every family, so it is
    a simulation input and the formula does not run.
    """
    capital_as_savings = draw(st.booleans())
    # £4,000 is neither a total of the reported amounts drawn here nor such a
    # total less tariff income, so it is always read as entered directly.
    esa_income = (
        draw(st.lists(st.sampled_from([0, 4_000, 4_000]), min_size=n, max_size=n))
        if draw(st.booleans())
        else None
    )
    return capital_as_savings, esa_income


def label(units, capital_as_savings, esa_income):
    """Record which input surfaces an example reaches (--hypothesis-show-statistics)."""
    event(
        "capital as household savings" if capital_as_savings else "assessable capital"
    )
    event("esa_income entered directly" if esa_income else "esa_income calculated")
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


def situation(units, capital_as_savings, esa_income):
    label(units, capital_as_savings, esa_income)
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
        if esa_income is not None:
            benunits[f"b{i}"]["esa_income"] = {YEAR: esa_income[i % len(esa_income)]}
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
    capital_as_savings, esa_income = data.draw(input_settings(len(drawn)))
    without = [(*family, None) for family, _ in drawn]
    with_extra = [(*family, extra) for family, extra in drawn]
    sim = Simulation(
        situation=situation(without + with_extra, capital_as_savings, esa_income)
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


def reference_eligibility(adults, dependants, capital, esa_income, sp_age, parameters):
    """The model's Income Support gate, read family by family."""
    IS = parameters.gov.dwp.income_support
    ESA = parameters.gov.dwp.ESA.income.capital
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
    single_with_placed_child = len(adults) == 1 and len(placed) > 0

    def is_claimant(adult, over_qualifying_age):
        carer = adult["receives_carer_benefit"] or adult["care_hours"] >= 35
        return (
            adult["income_support_reported"] > 0
            and (carer or lone_parent_with_young_child or single_with_placed_child)
            and not over_qualifying_age
            and adult["esa_contrib_reported"] == 0
        )

    if esa_income is not None:
        income_related_esa = esa_income > 0
    else:
        reported_esa = sum(a["esa_income_reported"] for a in adults)
        tariff = (
            math.ceil(
                max(0, capital - ESA.tariff_income.threshold) / ESA.tariff_income.step
            )
            * ESA.tariff_income.amount
            * 52
        )
        income_related_esa = (
            reported_esa > 0 and capital <= ESA.limit and reported_esa > tariff
        )
    return (
        any(is_claimant(a, s) for a, s in zip(adults, sp_age))
        and not income_related_esa
        and capital <= IS.means_test.capital.limit
    )


def explained_by_reports(esa_income, reported_total, capital, parameters):
    """Whether an esa_income equals what the reported amounts give: the
    award after the capital test, or their plain total."""
    ESA = parameters.gov.dwp.ESA.income.capital
    tariff = (
        math.ceil(
            max(0, capital - ESA.tariff_income.threshold) / ESA.tariff_income.step
        )
        * ESA.tariff_income.amount
        * 52
    )
    award = (
        max(0, reported_total - tariff)
        if reported_total > 0 and capital <= ESA.limit
        else 0
    )
    return abs(esa_income - award) <= 0.005 or abs(esa_income - reported_total) <= 0.005


@DIFFERENTIAL_SETTINGS
@given(FAMILIES, st.data())
def test_is_eligibility_matches_a_family_by_family_reading(drawn, data):
    capital_as_savings, esa_income = data.draw(input_settings(len(drawn)))
    units = [(*family, extra) for family, extra in drawn]
    sim = Simulation(situation=situation(units, capital_as_savings, esa_income))
    eligible = sim.calculate("income_support_eligible", YEAR)
    if eligible.any():
        event("some family eligible")
    sp_age = sim.calculate("is_SP_age", YEAR)
    parameters = sim.tax_benefit_system.parameters(YEAR)
    start = 0
    for i, (adults, dependants, capital, extra) in enumerate(units):
        # An esa_income the reported amounts explain is read through them,
        # like a calculated one.
        entered = None
        if esa_income is not None:
            reported_total = sum(
                member.get("esa_income_reported", 0) for member in adults + [extra]
            )
            if not explained_by_reports(
                esa_income[i], reported_total, capital, parameters
            ):
                entered = esa_income[i]
        expected = reference_eligibility(
            adults,
            dependants,
            capital,
            entered,
            sp_age[start : start + len(adults)],
            parameters,
        )
        assert eligible[i] == expected, units[i]
        start += len(adults) + len(dependants) + 1

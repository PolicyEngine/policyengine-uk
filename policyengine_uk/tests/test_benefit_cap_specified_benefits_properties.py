"""The benefit cap's specified-benefit exceptions follow the people the law names.

HB Regs 2006 reg 75F(1) and UC Regs 2013 reg 83(1) lift the cap where:

- the claimant or partner receives ESA that includes the support component
  (75F(1)(a); 83(1)(a)), industrial injuries benefit, attendance allowance
  or an armed forces compensation payment (75F(1)(b)-(d); 83(1)(b)-(e)). A
  Universal Credit claim ends the couple's income-related ESA (SI 2013/983
  art. 4), so a claiming family can count only contributory ESA;
- the claimant, partner or a child or young person they are responsible for
  receives disability living allowance (75F(1)(e); 83(1)(f));
- the claimant, partner or a young person they are responsible for receives
  personal independence payment, or is entitled to Carer's Allowance or
  Carer Support Payment (75F(1)(ea), (h), (ha); 83(1)(g), (i), (ia)): an
  award, or the model's Carer's Allowance conditions, 35 hours of care a
  week, whether or not it is paid (is_entitled_to_carer_benefit), or,
  for a Housing Benefit young person, armed forces independence payment
  (75F(1)(ea); UC counts it as attendance allowance, UC Regs 2013 reg 2);
- a Universal Credit claimant has limited capability for work and
  work-related activity or caring responsibilities, so the award includes the
  LCWRA or carer element (83(1)(a), (j); regs 27(1), 29(1)). An element
  entered for the award decides it alone: included when positive, whatever
  anyone's circumstances, and not included when entered as nil. So does the
  amount of an element a reform's formula gives, and the model's own
  element is included when positive unless only members who are not
  claimants have the circumstance. A person with
  ESA of their own whose ESA lacks the support component is inferred not to
  have limited capability for work-related activity (reg 40(1)(a)(ii));
- the claimant or couple is entitled to working tax credit (HB reg 75E(2)).

Each scheme applies its own exceptions. UC reg 83(1)(f) names a "child or
qualifying young person"; HB reg 75F(1)(e) names a "child or young person".
UC includes a 16-year-old school leaver (reg 5(1)(a)) who does not receive
benefits in their own right (reg 5(5)) and is not looked after (reg 4(6)).
HB young persons follow Child Benefit (reg 19), so only the education-based
young-person role counts for Housing Benefit below. UC reg 83(1)(c) names
"a claimant" for attendance allowance, which includes armed forces
independence payment (reg 2); HB reg 75F(1)(ea) also names "a young person"
for it. Only UC reg 83(1)(a), (j) names the LCWRA and carer elements; only
HB reg 75E(2) names entitlement to working tax credit.

Invariants:

1. Adding a member who is neither the claimant, the partner nor a child or
   young person they are responsible for never changes whether the family is
   exempt under either scheme, its caps, its reductions, its Universal Credit
   or its Housing Benefit, whatever disability or carer benefits, ESA, JSA,
   incapacity benefit, SDA, disability flag or caring that member has. The
   cap counts only the welfare benefits "to which the single person or
   couple is entitled" (UC Regs 2013 reg 80(1); HB Regs 2006 reg 75A). Nor
   do their age or earnings: Housing Benefit's age exception reads the
   claimant and partner (its pension-age regulations, HB Regs 2006 reg 5),
   Universal Credit's the claimants (SI 2014/1230 reg 60C), and the
   earnings exception the claimants (UC Regs 2013 reg 82(1)(a)), so the
   draws give the member State Pension age or earnings at times.
2. Each scheme's exemption equals its own reference written directly from
   the regulations, with claimant roles fixed and young-person status
   following each scheme's own exclusions (differential test).
   The union of the two equals the former shared reference.
3. A family exempt under a scheme has no cap and no reduction to that
   scheme's award; any other family has that scheme's statutory cap (UC reg
   80A(2); HB reg 75CA) and loses the excess: UC reg 81 deducts the
   childcare element from it, and HB reg 75D(2) leaves at least 50p a week.
4. Each head alone: for every role and every circumstance, a family whose
   only circumstance is that one, held by that member, is exempt exactly when
   that scheme's reference says (an exhaustive table, for each
   support-component mode).

The properties draw families at random; invariant 4 enumerates them. Each
example builds many families in one simulation, in separate households
and benefit units. Roles are given explicitly (is_claimant_or_partner). The
support component is set for every person in a simulation or for none, since
an input set for some people is given its default for the rest. For the same
reason, a simulation whose families may enter a UC element enters it as nil
for the families that do not.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, event, given, settings
from hypothesis import strategies as st

from policyengine_core.periods import YEAR as YEAR_PERIOD
from policyengine_core.periods import period
from policyengine_core.reforms import Reform
from policyengine_uk import Simulation
from policyengine_uk.model_api import BenUnit, Variable
from policyengine_uk.scenarios.uc_reform import REBALANCING_YEARS
from policyengine_uk.utils.supplied_inputs import set_model_value, supplied_input

YEAR = 2025
SINGLE_CAP, FAMILY_CAP = 14_753, 22_020  # Outside London, 2025-26.
# A month's element times 12, 2025-26: LCWRA 423.27, carer 201.46.
ENTERED_ELEMENTS = {"uc_LCWRA_element": 5_079.24, "uc_carer_element": 2_417.52}
SCHEMES = {
    "uc": {
        "specified": "is_uc_benefit_cap_exempt_specified_benefit",
        "exempt": "is_uc_benefit_cap_exempt",
        "cap": "uc_benefit_cap",
        "reduction": "uc_benefit_cap_reduction",
    },
    "hb": {
        "specified": "is_housing_benefit_benefit_cap_exempt_specified_benefit",
        "exempt": "is_housing_benefit_benefit_cap_exempt",
        "cap": "housing_benefit_benefit_cap",
        "reduction": "housing_benefit_benefit_cap_reduction",
    },
}

CLAIMANT_OR_PARTNER = ["attendance_allowance", "iidb_reported", "afcs_reported"]
CHILD_OR_YOUNG_PERSON = ["dla"]
YOUNG_PERSON = ["pip_dl", "carers_allowance", "carer_support_payment"]
HOUSING_BENEFIT_YOUNG_PERSON = ["armed_forces_independence_payment"]
AMOUNTS = (
    CLAIMANT_OR_PARTNER
    + CHILD_OR_YOUNG_PERSON
    + YOUNG_PERSON
    + HOUSING_BENEFIT_YOUNG_PERSON
)
# Capped welfare benefits that do not lift the cap (WRA 2012 s.96(10)).
CAPPED_REPORTS = {
    "jsa_contrib": "jsa_contrib_reported",
    "jsa_income": "jsa_income_reported",
    "incapacity_benefit": "incapacity_benefit_reported",
    "sda": "sda_reported",
}
OWN_RIGHT_REPORTS = (
    "universal_credit_reported",
    "esa_contrib_reported",
    "esa_income_reported",
    "jsa_contrib_reported",
    "jsa_income_reported",
)
CIRCUMSTANCES = AMOUNTS + [
    "esa_contrib",
    "esa_income",
    "caring",
    "disabled",
    *CAPPED_REPORTS,
]

ROLES = {
    "child": {"current_education": "PRIMARY"},
    "looked_after_child": {
        "current_education": "PRIMARY",
        "is_looked_after_by_local_authority": True,
    },
    "young_person": {"current_education": "UPPER_SECONDARY"},
    "sixteen": {"age": 16, "current_education": "NOT_IN_EDUCATION"},
    "sixteen_own_right": {
        "age": 16,
        "current_education": "NOT_IN_EDUCATION",
        "receives_benefits_in_own_right": True,
    },
}


def blank(role, age):
    person = {name: 0 for name in AMOUNTS}
    person.update(
        {
            "age": age,
            "esa_contrib_reported": 0,
            "esa_income_reported": 0,
            **{report: 0 for report in CAPPED_REPORTS.values()},
            "care_hours": 0,
            "employment_income": 0,
            "is_disabled_for_benefits": False,
            "current_education": "NOT_IN_EDUCATION",
            "_role": role,
        }
    )
    person.update(ROLES.get(role, {}))
    return person


def give(person, circumstance):
    set_circumstance(person, circumstance)
    event(f"{person['_role']} {circumstance}")


def set_circumstance(person, circumstance):
    if circumstance in AMOUNTS:
        person[circumstance] = 3_000
    elif circumstance == "esa_contrib":
        person["esa_contrib_reported"] = 5_000
    elif circumstance == "esa_income":
        person["esa_income_reported"] = 4_000
    elif circumstance in CAPPED_REPORTS:
        person[CAPPED_REPORTS[circumstance]] = 2_000
    elif circumstance == "caring":
        person["care_hours"] = 35
    else:
        person["is_disabled_for_benefits"] = True


@st.composite
def families(draw, supplied, enter_elements):
    """A claimant, an optional partner, up to three dependants and a
    non-dependent adult, with at most two circumstances among them, and the
    family's benefit-unit inputs."""
    members = [blank(role="claimant", age=draw(st.integers(25, 60)))]
    if draw(st.booleans()):
        members.append(blank(role="claimant", age=draw(st.integers(25, 60))))
    for _ in range(draw(st.integers(0, 3))):
        role = draw(st.sampled_from(sorted(ROLES)))
        if role in ("child", "looked_after_child"):
            age = draw(st.integers(0, 15))
        elif role == "young_person":
            age = draw(st.integers(16, 18))
        else:
            age = 16
        members.append(blank(role, age))
    has_dependants = any(m["_role"] != "claimant" for m in members)
    for member in members:
        if member["_role"] == "claimant":
            member["is_parent"] = has_dependants
    other = blank(
        role="other", age=draw(st.one_of(st.integers(17, 60), st.integers(67, 80)))
    )
    other["employment_income"] = draw(st.sampled_from([0, 0, 0, 25_000]))
    event(f"other aged 67+: {other['age'] >= 67}")
    event(f"other earns: {other['employment_income'] > 0}")
    for _ in range(draw(st.integers(0, 2))):
        give(draw(st.sampled_from(members)), draw(st.sampled_from(CIRCUMSTANCES)))
    for _ in range(draw(st.integers(1, 2))):
        give(other, draw(st.sampled_from(CIRCUMSTANCES)))
    if supplied:
        for person in members + [other]:
            person["esa_includes_support_component"] = draw(st.booleans())
    benunit_inputs = {"working_tax_credit": draw(st.sampled_from([0] * 9 + [500]))}
    if enter_elements:
        entered = draw(st.sampled_from([None, *ENTERED_ELEMENTS]))
        event(f"entered element: {entered}")
        for element, amount in ENTERED_ELEMENTS.items():
            benunit_inputs[element] = amount if element == entered else 0
    return members, other, benunit_inputs


@st.composite
def draws(draw):
    """Families in one simulation, sharing whether the support component is
    supplied and whether UC elements are entered."""
    supplied = draw(st.booleans())
    enter_elements = draw(st.booleans())
    event(f"support component supplied: {supplied}")
    return draw(st.lists(families(supplied, enter_elements), min_size=1, max_size=6))


def situation(units, year=YEAR, extra_benunit=None):
    people, benunits, households = {}, {}, {}
    for i, (members, benunit_inputs) in enumerate(units):
        names = []
        for j, inputs in enumerate(members):
            name = f"p{i}_{j}"
            people[name] = {
                k: {year: v} for k, v in inputs.items() if not k.startswith("_")
            }
            people[name]["is_claimant_or_partner"] = {
                year: inputs["_role"] == "claimant"
            }
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            **{k: {year: v} for k, v in benunit_inputs.items()},
            **{k: {year: v} for k, v in (extra_benunit or {}).items()},
        }
        households[f"h{i}"] = {
            "members": names,
            "region": {year: "NORTH_EAST"},
            "country": {year: "ENGLAND"},
        }
    return {"people": people, "benunits": benunits, "households": households}


def own_esa(m):
    return m["esa_contrib_reported"] > 0 or m["esa_income_reported"] > 0


def own_benefits(m):
    # UC reg 5(5): a personal report identifies an award in the person's own right.
    return any(m.get(report, 0) > 0 for report in OWN_RIGHT_REPORTS)


def reference_specified_benefit(members, benunit_inputs, scheme):
    """UC Regs 2013 reg 83(1) or HB Regs 2006 reg 75F(1), read directly, with
    roles known by construction."""
    claimants = [m for m in members if m["_role"] == "claimant"]
    # UC reg 83 names a "qualifying young person" (reg 5), which includes a
    # 16-year-old school leaver (reg 5(1)(a)); HB reg 75F names a "young
    # person" (reg 19), a Child Benefit qualifying young person. The
    # school-leaver role here has no Child Benefit education or terminal-date
    # circumstance, so it is not one.
    young_roles = ("young_person", "sixteen") if scheme == "uc" else ("young_person",)
    # The UC predicate supplements its qualifying-young-person test with a
    # separate age-16 approximation, which reads only the explicit own-right
    # flag. Reported awards remove older UC young persons, but do not change
    # that approximation or the Housing Benefit test.
    young_persons = [
        m
        for m in members
        if m["_role"] in young_roles
        and (scheme != "uc" or m["age"] == 16 or not own_benefits(m))
    ]
    children = [m for m in members if m["_role"] == "child"]
    # No capital, so the couple's income-related award is their reports,
    # unless the family claims Universal Credit: the claim ends it (SI
    # 2013/983 art. 4; esa_income_report_closed). would_claim_uc defaults to
    # true.
    claims_uc = benunit_inputs.get("would_claim_uc", True)
    couple_award = not claims_uc and any(
        m["esa_income_reported"] > 0 for m in claimants
    )

    def support_component(m):
        # Supplied, or assumed for anyone with their own allowance.
        return m.get("esa_includes_support_component", own_esa(m))

    def receives_esa_with_support_component(m):
        # The couple's income-related award is payable to the member who
        # reports it (HB Regs 2006 reg 2(3A)).
        receiving = m["esa_contrib_reported"] > 0 or (
            couple_award and m["esa_income_reported"] > 0
        )
        return receiving and support_component(m)

    def lcwra(m):
        # UC Regs 2013 reg 40(1)(a)(ii): an ESA award without the support
        # component means the ESA assessment found no LCWRA.
        no_support = own_esa(m) and not support_component(m)
        return m["is_disabled_for_benefits"] and not no_support

    def entitled_to_carer_benefit(m):
        # "Entitled to" Carer's Allowance or Carer Support Payment (75F(1)(h),
        # (ha); 83(1)(i), (ia)): an award, or the 35 hours of care a week that
        # the model's Carer's Allowance conditions test (in England, where
        # every family here lives, and for anyone who would claim, the
        # default). Those conditions do not apply the full-time education
        # exclusion (SSCBA 1992 s.70(3)), so a young person in education who
        # cares 35 hours counts as entitled.
        return (
            m["care_hours"] >= 35
            or m["carers_allowance"] > 0
            or m["carer_support_payment"] > 0
        )

    def carer(m):
        # Caring responsibilities for the UC carer element (UC Regs 2013 reg
        # 30): the same 35 hours, or a carer benefit.
        return entitled_to_carer_benefit(m)

    def any_receives(people, benefits):
        return any(m[b] > 0 for m in people for b in benefits)

    def element_included(element, circumstance):
        # Reg 83(1)(a), (j): the element is included in the award. An element
        # entered for the award decides it; otherwise a claimant's
        # circumstances give it (regs 27(1), 29(1)).
        if element in benunit_inputs:
            return benunit_inputs[element] > 0
        return any(circumstance(m) for m in claimants)

    common = (
        any(receives_esa_with_support_component(m) for m in claimants)
        or any_receives(claimants, CLAIMANT_OR_PARTNER)
        or any_receives(claimants + children + young_persons, CHILD_OR_YOUNG_PERSON)
        or any_receives(claimants + young_persons, ["pip_dl"])
        or any(entitled_to_carer_benefit(m) for m in claimants + young_persons)
    )
    if scheme == "hb":
        # HB reg 75F(1)(ea): armed forces independence payment of the
        # claimant, partner or a young person.
        return common or any_receives(
            claimants + young_persons, HOUSING_BENEFIT_YOUNG_PERSON
        )
    # UC reg 83(1)(c): attendance allowance, which includes armed forces
    # independence payment (reg 2), of "a claimant"; and the LCWRA and carer
    # elements (reg 83(1)(a), (j)), which only Universal Credit has.
    return (
        common
        or any_receives(claimants, HOUSING_BENEFIT_YOUNG_PERSON)
        or element_included("uc_LCWRA_element", lcwra)
        or element_included("uc_carer_element", carer)
    )


def reference_exempt(members, benunit_inputs, scheme):
    """The scheme's exemption. HB reg 75E(2): the claimant or couple is
    entitled to working tax credit; Universal Credit has no such exception.
    The claimants are under the qualifying age for State Pension Credit and
    have no earnings, so neither the age exceptions (HB reg 5; SI 2014/1230
    reg 60C) nor the earnings exception (UC reg 82) applies."""
    return reference_specified_benefit(members, benunit_inputs, scheme) or (
        scheme == "hb" and benunit_inputs["working_tax_credit"] > 0
    )


def reference_union(members, benunit_inputs):
    """The former shared reference: either scheme's exemption."""
    return reference_exempt(members, benunit_inputs, "uc") or reference_exempt(
        members, benunit_inputs, "hb"
    )


def reference_cap(members, scheme):
    # Each scheme's rate: a single claimant (UC reg 80A(2)(c)) or a claimant
    # who neither has a partner nor is a lone parent (HB regs 2(1), 75CA(2)),
    # with no child or young person. The family-rate helper counts any
    # 16-year-old for the year (UC reg 5(1)(a); for HB, Child Benefit's
    # school-leaver terminal dates, which annual ages cannot place); it does
    # not yet apply reg 5(5) to one receiving benefits in their own right.
    # Older UC young persons cease to count when they report their own award;
    # Housing Benefit continues to read the existing Child Benefit test.
    claimants = sum(m["_role"] == "claimant" for m in members)
    dependants = any(
        m["_role"] in ("child", "sixteen", "sixteen_own_right")
        or (
            m["_role"] == "young_person"
            and (scheme != "uc" or m["age"] == 16 or not own_benefits(m))
        )
        for m in members
    )
    return SINGLE_CAP if claimants == 1 and not dependants else FAMILY_CAP


CAPPED_FAMILY = {
    "child_tax_credit": 0,
    "child_benefit": 0,
    "income_support": 0,
    "uc_childcare_element": 0,
}


def capped_family(scheme):
    """30,000 of the scheme's award before the cap and none of the other's;
    the other family-level capped benefits are nil, so the capped total is
    the award plus whatever the claimant's and partner's own benefits add.
    The family claims Universal Credit exactly when it is on it, so the
    couple's income-related ESA continues only on Housing Benefit."""
    return {
        **CAPPED_FAMILY,
        "would_claim_uc": scheme == "uc",
        "universal_credit_pre_benefit_cap": 30_000 if scheme == "uc" else 0,
        "housing_benefit_pre_benefit_cap": 30_000 if scheme == "hb" else 0,
        # This supplied award exercises the cap independently of take-up;
        # another member's reports must not mask its final Housing Benefit.
        "would_claim_housing_benefit": scheme == "hb",
    }


def by_scheme(units):
    """The units twice, first on Universal Credit and then on Housing
    Benefit, each in its own benefit units."""
    return [
        (members, {**inputs, **capped_family(scheme)})
        for scheme in SCHEMES
        for members, inputs in units
    ]


SETTINGS = settings(
    max_examples=40,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@SETTINGS
@given(draws())
def test_non_dependent_adults_never_change_the_exemption(drawn):
    without = [(members, inputs) for members, _, inputs in drawn]
    with_other = [(members + [other], inputs) for members, other, inputs in drawn]
    # Each family on Universal Credit and, separately, on Housing Benefit:
    # [UC without, UC with, HB without, HB with], k families each.
    units = by_scheme(without + with_other)
    sim = Simulation(situation=situation(units))
    k = len(drawn)
    claimant_or_partner = sim.calculate("is_claimant_or_partner", YEAR)
    legacy = sim.calculate("is_child_or_young_person_for_legacy_benefits", YEAR)
    uc = sim.calculate("is_child_or_qualifying_young_person_for_universal_credit", YEAR)
    sizes = [len(members) for members, _ in units]
    starts = np.cumsum([0] + sizes[:-1])
    for offset in (0, 2 * k):
        for i in range(k):
            # The added member is the last of its benefit unit: neither
            # claimant, partner nor anyone's dependant.
            family = offset + k + i
            last = starts[family] + sizes[family] - 1
            assert not (claimant_or_partner[last] or legacy[last] or uc[last]), drawn[i]
    # The model pays one scheme's award, so the family's reduction is that
    # scheme's.
    reduction = sim.calculate("benefit_cap_reduction", YEAR)
    for group, scheme in enumerate(SCHEMES):
        other_scheme = "hb" if scheme == "uc" else "uc"
        part = slice(group * 2 * k, (group + 1) * 2 * k)
        assert not sim.calculate(SCHEMES[other_scheme]["reduction"], YEAR)[part].any()
        assert np.array_equal(
            reduction[part], sim.calculate(SCHEMES[scheme]["reduction"], YEAR)[part]
        )
    for variable in [
        *(name for names in SCHEMES.values() for name in names.values()),
        "is_uc_benefit_cap_exempt_earnings",
        "is_uc_benefit_cap_exempt_qualifying_age",
        "housing_benefit_pension_age_regulations_apply",
        "benefit_cap_welfare_benefits",
        "benefit_cap_reduction",
        "universal_credit",
        "housing_benefit",
    ]:
        values = sim.calculate(variable, YEAR)
        for offset in (0, 2 * k):
            for i in range(k):
                assert values[offset + i] == values[offset + k + i], (
                    variable,
                    drawn[i],
                )


@SETTINGS
@given(draws())
def test_exemption_matches_regulations(drawn):
    units = [(members + [other], inputs) for members, other, inputs in drawn]
    sim = Simulation(situation=situation(units))
    overall = {}
    for scheme, names in SCHEMES.items():
        specified = sim.calculate(names["specified"], YEAR)
        overall[scheme] = sim.calculate(names["exempt"], YEAR)
        for i, (members, inputs) in enumerate(units):
            expected = reference_specified_benefit(members, inputs, scheme)
            event(f"{scheme} reference exempt: {expected}")
            assert specified[i] == expected, (scheme, units[i])
            assert overall[scheme][i] == reference_exempt(members, inputs, scheme), (
                scheme,
                units[i],
            )
    # Either scheme's exemption: the former shared reference.
    union = overall["uc"] | overall["hb"]
    for i, (members, inputs) in enumerate(units):
        assert union[i] == reference_union(members, inputs), units[i]


@SETTINGS
@given(draws())
def test_exempt_families_have_no_cap_and_others_the_statutory_cap(drawn):
    units = [(members + [other], inputs) for members, other, inputs in drawn]
    # 30,000 of either award alone exceeds either cap. The other family-level
    # capped benefits are set to nil; they only add to the excess.
    k = len(units)
    sim = Simulation(situation=situation(by_scheme(units)))
    total = sim.calculate("benefit_cap_welfare_benefits", YEAR)
    for group, (scheme, names) in enumerate(SCHEMES.items()):
        part = slice(group * k, (group + 1) * k)
        exempt = sim.calculate(names["exempt"], YEAR)[part]
        cap = sim.calculate(names["cap"], YEAR)[part]
        reduction = sim.calculate(names["reduction"], YEAR)[part]
        for i, (members, _) in enumerate(units):
            if exempt[i]:
                assert np.isinf(cap[i]) and reduction[i] == 0, (scheme, units[i])
            else:
                assert cap[i] == reference_cap(members, scheme), (scheme, units[i])
                excess = max(total[part][i] - cap[i], 0)
                # UC reg 81: the excess less the childcare element (nil
                # here). HB reg 75D(2): no more than leaves reg 75's 50p a
                # week, 30,000 - 0.50 x 52.
                expected = excess if scheme == "uc" else min(excess, 30_000 - 26)
                assert reduction[i] == pytest.approx(expected, abs=0.01), (
                    scheme,
                    units[i],
                )
                assert reduction[i] >= 30_000 - cap[i] - 0.01, (scheme, units[i])


SINGLE_HEAD_ROLES = ["claimant", "partner", *sorted(ROLES), "other"]


def single_head_units(mode):
    """One family per (role, circumstance): a claimant and, unless the role is
    the claimant, one more member holding the circumstance."""
    units = []
    for role in SINGLE_HEAD_ROLES:
        for circumstance in CIRCUMSTANCES:
            claimant = blank(role="claimant", age=40)
            if role == "claimant":
                holder, members = claimant, [claimant]
            else:
                age = {"partner": 38, "other": 30, "young_person": 17}.get(role, 10)
                holder = blank("claimant" if role == "partner" else role, age)
                members = [claimant, holder]
            set_circumstance(holder, circumstance)
            claimant["is_parent"] = role not in ("claimant", "partner", "other")
            if mode is not None:
                for person in members:
                    person["esa_includes_support_component"] = mode
            units.append(((role, circumstance), members))
    return units


@pytest.mark.parametrize("mode", [None, True, False])
def test_each_head_alone_matches_regulations(mode):
    units = single_head_units(mode)
    no_entries = {"working_tax_credit": 0}
    sim = Simulation(
        situation=situation([(members, no_entries) for _, members in units])
    )
    exemptions = {}
    for scheme, names in SCHEMES.items():
        exempt = sim.calculate(names["specified"], YEAR)
        exemptions[scheme] = exempt
        mismatches = [
            (scheme, key, bool(exempt[i]))
            for i, (key, members) in enumerate(units)
            if exempt[i] != reference_specified_benefit(members, no_entries, scheme)
        ]
        assert not mismatches, mismatches
        # Both outcomes occur under each scheme.
        assert exempt.any() and not exempt.all()
    # The schemes differ: UC's elements and 16-year-old school leaver, HB's
    # young person's armed forces independence payment.
    assert (exemptions["uc"] != exemptions["hb"]).any()
    # Every role meets every circumstance.
    assert len(units) == len(SINGLE_HEAD_ROLES) * len(CIRCUMSTANCES)


def element_reform(element, amount):
    """A reform whose formula for ``element`` gives ``amount`` to every family."""
    replacement = type(
        element,
        (Variable,),
        {
            "value_type": float,
            "entity": BenUnit,
            "definition_period": YEAR_PERIOD,
            "label": f"{element} (test reform)",
            "formula": lambda benunit, period, parameters: benunit.filled_array(amount),
        },
    )

    class ReplaceElement(Reform):
        def apply(self):
            self.update_variable(replacement)

    return ReplaceElement


# The Universal Credit exception the elements give (UC Regs 2013 reg
# 83(1)(a), (j)); Housing Benefit has no element exception.
UC_SPECIFIED = SCHEMES["uc"]["specified"]

# The circumstance that gives each element (UC Regs 2013 regs 27(1), 29(1)).
# The carer flag is set directly, with no hours of care, so that no
# entitlement to Carer's Allowance lifts the cap by another route.
ELEMENT_CIRCUMSTANCES = {
    "uc_LCWRA_element": "uc_limited_capability_for_WRA",
    "uc_carer_element": "is_carer_for_benefits",
}


@pytest.mark.parametrize("element", sorted(ELEMENT_CIRCUMSTANCES))
def test_an_element_a_reform_gives_is_decided_by_its_value(element):
    """Reg 83(1)(a), (j): an element a reform's formula puts in the award lifts
    the cap whatever another member's circumstances, and a reform that gives
    nil removes the exception the claimant's circumstance would give."""
    circumstance = ELEMENT_CIRCUMSTANCES[element]
    claimant, other = blank(role="claimant", age=40), blank(role="other", age=30)
    other[circumstance] = True
    positive = Simulation(
        situation=situation([([claimant, other], {"working_tax_credit": 0})]),
        reform=element_reform(element, 6_000),
    )
    assert positive.calculate(element, YEAR)[0] == 6_000
    assert positive.calculate(UC_SPECIFIED, YEAR)[0]
    # A reform's amount that equals the model's own (here, what the model's
    # formula gives for a claimant's circumstance; it gives nothing for the
    # other member's, regs 27(1), 29(1)) is still the reform's.
    assert (
        Simulation(
            situation=situation([([claimant, other], {"working_tax_credit": 0})])
        ).calculate(element, YEAR)[0]
        == 0
    )
    claimant_with_circumstance = blank(role="claimant", age=40)
    claimant_with_circumstance[circumstance] = True
    model_amount = Simulation(
        situation=situation(
            [([claimant_with_circumstance, other], {"working_tax_credit": 0})]
        )
    ).calculate(element, YEAR)[0]
    assert model_amount > 0
    same = Simulation(
        situation=situation([([claimant, other], {"working_tax_credit": 0})]),
        reform=element_reform(element, model_amount),
    )
    assert same.calculate(element, YEAR)[0] == model_amount
    assert same.calculate(UC_SPECIFIED, YEAR)[0]

    claimant = blank(role="claimant", age=40)
    claimant[circumstance] = True
    nil = Simulation(
        situation=situation([([claimant], {"working_tax_credit": 0})]),
        reform=element_reform(element, 0),
    )
    assert nil.calculate(element, YEAR)[0] == 0
    assert not nil.calculate(UC_SPECIFIED, YEAR)[0]
    # Without the reform the claimant's circumstance gives the element and
    # lifts the cap.
    baseline = Simulation(
        situation=situation([([claimant], {"working_tax_credit": 0})])
    )
    assert baseline.calculate(element, YEAR)[0] > 0
    assert baseline.calculate(UC_SPECIFIED, YEAR)[0]


def test_the_rebalancing_adds_no_entry_and_keeps_one():
    """From 2026 the Universal Credit rebalancing rescales uc_LCWRA_element
    (scenarios/uc_reform.py). An element it rescales from the model's own
    formula is not an entry: the claimant's limited capability gives one that
    lifts the cap, and the other member's gives none (reg 27(1)); an element
    entered for the award stays entered."""
    year = 2026
    claimant, other = blank(role="claimant", age=40), blank(role="other", age=30)
    for holder in ["claimant", "other"]:
        claimant_flag, other_flag = dict(claimant), dict(other)
        (claimant_flag if holder == "claimant" else other_flag)[
            "uc_limited_capability_for_WRA"
        ] = True
        calculated = Simulation(
            situation=situation(
                [([claimant_flag, other_flag], {"working_tax_credit": 0})], year
            )
        )
        positive = calculated.calculate("uc_LCWRA_element", year)[0] > 0
        assert positive == (holder == "claimant")
        benunit = calculated.populations["benunit"]
        assert supplied_input(benunit, "uc_LCWRA_element", period(year)) is None
        assert bool(calculated.calculate(UC_SPECIFIED, year)[0]) == positive
    other["uc_limited_capability_for_WRA"] = True

    entered = Simulation(
        situation=situation(
            [([claimant, other], {"working_tax_credit": 0, "uc_LCWRA_element": 5_000})],
            year,
        )
    )
    benunit = entered.populations["benunit"]
    assert supplied_input(benunit, "uc_LCWRA_element", period(year)) is not None
    assert entered.calculate(UC_SPECIFIED, year)[0]


# An element is an entry only while the value stored is one: the model's own
# value (set_model_value) stops counting as the model's once anything else is
# stored for the period, so an entry equal to it is still an entry.


# The model's own amount stored below for a family whose only member with
# limited capability is not a claimant: twelve months at the 2026-27 rate.
MODEL_OWNED_ELEMENT = 217.26 * 12


def element_situation(year, element=None):
    """A claimant and a non-claimant adult with limited capability. The
    model's formula gives no element for the other member's limited
    capability (reg 27(1)); ``model_owned`` stores one as the model's own."""
    claimant, other = blank(role="claimant", age=40), blank(role="other", age=30)
    other["uc_limited_capability_for_WRA"] = True
    inputs = {"working_tax_credit": 0}
    if element is not None:
        inputs["uc_LCWRA_element"] = element
    return situation([([claimant, other], inputs)], year)


def model_owned(year):
    """A simulation of ``element_situation`` for ``year`` holding a positive
    element stored as the model's own (set_model_value, as the rebalancing
    stores the amounts it rescales) although only the non-claimant has
    limited capability. Such an element is not included in the award, so it
    does not lift the cap; an entry of the same amount is, and does."""
    simulation = Simulation(situation=element_situation(year))
    set_model_value(
        simulation, "uc_LCWRA_element", year, np.array([MODEL_OWNED_ELEMENT])
    )
    return simulation


def is_entered(simulation, year):
    benunit = simulation.populations["benunit"]
    return supplied_input(benunit, "uc_LCWRA_element", period(year)) is not None


def enter_with_set_input(simulation, year, amount):
    simulation.set_input("uc_LCWRA_element", year, [amount])


def enter_the_calculated_array(simulation, year, amount):
    # The array the engine returns for the period, stored back as it is.
    simulation.set_input(
        "uc_LCWRA_element", year, simulation.calculate("uc_LCWRA_element", year)
    )


def enter_after_deleting(simulation, year, amount):
    simulation.delete_arrays("uc_LCWRA_element", year)
    simulation.set_input("uc_LCWRA_element", year, [amount])


def enter_by_rebuilding_from_a_situation(simulation, year, amount):
    simulation.build_from_situation(element_situation(year, amount))


def enter_by_rebuilding_from_a_frame(simulation, year, amount):
    frame = Simulation(situation=element_situation(year)).to_input_dataframe()
    # A situation sets no identifiers. The two people share a benefit unit
    # and a household.
    frame[f"person_id__{year}"] = [1, 2]
    frame[f"benunit_id__{year}"] = 1
    frame[f"household_id__{year}"] = 1
    frame[f"uc_LCWRA_element__{year}"] = amount
    simulation.build_from_dataframe(frame)


@pytest.mark.parametrize(
    "enter",
    [
        enter_with_set_input,
        enter_the_calculated_array,
        enter_after_deleting,
        enter_by_rebuilding_from_a_situation,
        enter_by_rebuilding_from_a_frame,
    ],
)
def test_an_entry_equal_to_the_model_value_is_an_entry(enter):
    """Reg 83(1)(a): an element entered for the award decides the exception,
    even one equal to the amount the rebalancing stored as the model's in the
    same simulation, however it is entered."""
    year = 2026
    without_entry = model_owned(year)
    assert not without_entry.calculate(UC_SPECIFIED, year)[0]
    simulation = model_owned(year)
    model_amount = float(simulation.calculate("uc_LCWRA_element", year)[0])
    assert model_amount > 0
    assert not is_entered(simulation, year)

    # The exemption is calculated only after the entry: the engine does not
    # recalculate a cached value when an input it depends on changes.
    enter(simulation, year, model_amount)
    assert simulation.calculate("uc_LCWRA_element", year)[0] == pytest.approx(
        model_amount
    )
    assert is_entered(simulation, year)
    assert simulation.calculate(UC_SPECIFIED, year)[0]
    # As in a simulation built with the entry.
    fresh = Simulation(situation=element_situation(year, model_amount))
    assert is_entered(fresh, year)
    assert fresh.calculate(UC_SPECIFIED, year)[0]


def test_clones_and_branches_keep_their_own_record_of_model_values():
    year = 2026
    simulation = model_owned(year)
    model_amount = float(simulation.calculate("uc_LCWRA_element", year)[0])

    clone = simulation.clone()
    assert not is_entered(clone, year)
    set_model_value(clone, "uc_LCWRA_element", year, np.array([1_000.0]))
    assert not is_entered(clone, year)
    clone.set_input("uc_LCWRA_element", year, [model_amount])
    assert is_entered(clone, year)

    branch = simulation.get_branch("entry")
    assert not is_entered(branch, year)
    branch.set_input("uc_LCWRA_element", year, [model_amount])
    assert is_entered(branch, year)

    # Nothing the clone or the branch stored changes what the simulation reads.
    assert not is_entered(simulation, year)
    assert simulation.calculate("uc_LCWRA_element", year)[0] == pytest.approx(
        model_amount
    )
    assert not simulation.calculate(UC_SPECIFIED, year)[0]


@pytest.fixture(scope="module")
def rebalanced():
    year = 2026
    # The situation gives the non-claimant limited capability for 2026 only,
    # so the model's own element is stored for that year; later years keep
    # the formula's nil.
    simulation = model_owned(year)
    return simulation, float(simulation.calculate("uc_LCWRA_element", year)[0])


REBALANCED_YEARS = list(REBALANCING_YEARS)


@pytest.mark.parametrize(
    "input_period, amount, entered_years",
    [
        # Stored under the longer period, which no single year reads.
        ("year:2026:2", "model", []),
        ("year:2026:2", 10_000.0, []),
        ("year:2025:2", 999.0, []),
        ("year:2029:2", 999.0, []),
        # Consistent with the year's value, so nothing is stored.
        ("2026-01", "model", []),
        ("month:2026-01:12", "model", []),
        # Overlaps 2026 without being a year: nothing stored there.
        ("year:2026-04", 999.0, []),
        # Stored for the year itself.
        ("2027", 999.0, [2027]),
        ("2026", "model", [2026]),
    ],
)
def test_an_input_makes_the_element_an_entry_only_in_years_it_stores(
    rebalanced, input_period, amount, entered_years
):
    """The rebalancing stores the model's element for each rebalancing year. An input
    for another period that leaves a year's stored value in place leaves it
    the model's, so the non-claimant's limited capability still does not
    lift the cap that year; an input stored for the year is an entry, even
    the model's own amount."""
    base, model_amount = rebalanced
    simulation = base.clone()
    for year in REBALANCED_YEARS:
        assert not is_entered(simulation, year)
    value = model_amount if amount == "model" else amount
    simulation.set_input("uc_LCWRA_element", input_period, [value])
    for year in REBALANCED_YEARS:
        entered = year in entered_years
        assert is_entered(simulation, year) == entered, year
        assert simulation.calculate(UC_SPECIFIED, year)[0] == entered, year


def test_an_inconsistent_input_for_part_of_a_year_keeps_the_model_value(
    rebalanced,
):
    base, model_amount = rebalanced
    simulation = base.clone()
    with pytest.raises(ValueError, match="Inconsistent input"):
        simulation.set_input("uc_LCWRA_element", "2026-01", [model_amount + 1])
    assert not is_entered(simulation, 2026)


AMOUNT_NAMES = st.sampled_from(["model", "nil", "other"])
OPERATIONS = st.lists(
    st.one_of(
        st.tuples(st.just("model"), AMOUNT_NAMES),
        st.tuples(st.just("input"), AMOUNT_NAMES),
        st.tuples(st.just("longer"), AMOUNT_NAMES),
        st.tuples(st.just("month"), AMOUNT_NAMES),
        st.just(("delete",)),
        st.just(("rebuild",)),
        st.just(("clone",)),
    ),
    min_size=1,
    max_size=6,
)


@settings(
    max_examples=30,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(operations=OPERATIONS)
def test_an_element_is_entered_exactly_when_its_last_store_was_supplied(
    rebalanced, operations
):
    """Whatever the order of stores, deletions, rebuilds and clones, the
    element is an entry exactly when its value was last set as an input, or
    adjusted by the model after an input (set_model_value keeps an entry an
    entry). An input for a longer period, or for part of the year, that
    stores nothing for the year changes nothing. Stores in a clone never
    change what the simulation it was cloned from reads. The amounts include
    the model's own, so an entry equal to it is drawn."""
    year = 2026
    base, model_amount = rebalanced
    amounts = {"model": model_amount, "nil": 0.0, "other": 4_321.0}
    # The reference: whether the year's value is an entry, and the value
    # stored for the year (None once nothing is).
    simulation, entered, stored = base.clone(), False, model_amount
    earlier = []
    for operation in operations:
        event(operation[0])
        if operation[0] == "model":
            set_model_value(
                simulation,
                "uc_LCWRA_element",
                year,
                np.array([amounts[operation[1]]]),
            )
            stored = amounts[operation[1]]
        elif operation[0] == "input":
            simulation.set_input("uc_LCWRA_element", year, [amounts[operation[1]]])
            entered, stored = True, amounts[operation[1]]
        elif operation[0] == "longer":
            # Stored under year:2026:2, which a calculation for 2026 does not
            # read.
            simulation.set_input(
                "uc_LCWRA_element", f"year:{year}:2", [amounts[operation[1]]]
            )
        elif operation[0] == "month":
            amount = amounts[operation[1]]
            if stored is None:
                # A year with no input takes the month's value.
                simulation.set_input("uc_LCWRA_element", f"{year}-01", [amount])
                entered, stored = True, amount
            elif amount == stored:
                # Consistent with the year's value: nothing is stored.
                simulation.set_input("uc_LCWRA_element", f"{year}-01", [amount])
            else:
                with pytest.raises(ValueError, match="Inconsistent input"):
                    simulation.set_input("uc_LCWRA_element", f"{year}-01", [amount])
        elif operation[0] == "delete":
            simulation.delete_arrays("uc_LCWRA_element", year)
            entered, stored = False, None
        elif operation[0] == "rebuild":
            simulation.build_from_situation(element_situation(year))
            entered, stored = False, None
        else:
            earlier.append((simulation, entered))
            simulation = simulation.clone()
        assert is_entered(simulation, year) == entered, operations
    for clone_source, was_entered in earlier:
        assert is_entered(clone_source, year) == was_entered, operations


@pytest.mark.parametrize("year", [2025, 2026])
@pytest.mark.parametrize("active", [False, True])
@pytest.mark.parametrize("holder_role", ["claimant", "other"])
def test_internal_lcwra_wrapper_keeps_the_model_claimant_filter(
    year, active, holder_role
):
    """An internal amount wrapper does not turn nonclaimant circumstances into an award."""
    from policyengine_uk.model_api import Scenario
    from policyengine_uk.scenarios.uc_reform import add_universal_credit_reform

    claimant, other = blank("claimant", 40), blank("other", 30)
    (claimant if holder_role == "claimant" else other)[
        "uc_limited_capability_for_WRA"
    ] = True
    sim = Simulation(
        situation=situation([([claimant, other], {"working_tax_credit": 0})], year),
        scenario=Scenario(
            parameter_changes={"gov.dwp.universal_credit.rebalancing.active": active},
            applied_before_data_load=True,
        ),
    )
    # The model's formula gives the element only for a claimant (reg 27(1)).
    assert (sim.calculate("uc_LCWRA_element", year)[0] > 0) == (
        holder_role == "claimant"
    )
    assert not is_entered(sim, year)
    assert bool(sim.calculate(UC_SPECIFIED, year)[0]) == (holder_role == "claimant")
    add_universal_credit_reform(sim)
    sim.delete_arrays(UC_SPECIFIED, year)
    assert bool(sim.calculate(UC_SPECIFIED, year)[0]) == (holder_role == "claimant")


@pytest.mark.parametrize("active", [False, True])
@pytest.mark.parametrize("amount", [0, 5_000])
def test_internal_lcwra_wrapper_keeps_explicit_positive_and_nil_entries(active, amount):
    from policyengine_uk.model_api import Scenario

    sim = Simulation(
        situation=element_situation(2026, amount),
        scenario=Scenario(
            parameter_changes={"gov.dwp.universal_credit.rebalancing.active": active},
            applied_before_data_load=True,
        ),
    )
    assert is_entered(sim, 2026)
    assert bool(sim.calculate(UC_SPECIFIED, 2026)[0]) == (amount > 0)


@pytest.mark.parametrize("year", [2025, 2026])
@pytest.mark.parametrize("amount", [0, 6_000])
@pytest.mark.parametrize("when", ["constructor", "after_internal_wrapper"])
def test_internal_lcwra_wrapper_preserves_real_external_formula_origin(
    year, amount, when
):
    from policyengine_uk.model_api import Scenario
    from policyengine_uk.variables.gov.dwp.universal_credit.benefit_cap.is_uc_benefit_cap_exempt_specified_benefit import (
        calculated_by,
        uc_LCWRA_element as model_lcwra_element,
    )
    from policyengine_uk.scenarios.uc_reform import add_universal_credit_reform

    reform = element_reform("uc_LCWRA_element", amount)
    sim = Simulation(
        situation=element_situation(year),
        reform=reform if when == "constructor" else None,
    )
    if when == "after_internal_wrapper":
        Scenario.from_reform(reform).apply(sim)
    # Origin/formula unit precondition: discard the previously model-owned
    # award. This does not certify structural-reform public cache invalidation.
    sim.delete_arrays("uc_LCWRA_element", year)
    assert sim.calculate("uc_LCWRA_element", year)[0] == amount
    assert not calculated_by(
        sim.populations["benunit"],
        "uc_LCWRA_element",
        period(year),
        model_lcwra_element,
    )
    assert bool(sim.calculate(UC_SPECIFIED, year)[0]) == (amount > 0)
    add_universal_credit_reform(sim)
    sim.delete_arrays(UC_SPECIFIED, year)
    # Origin/formula unit precondition: discard the previously model-owned
    # award. This does not certify structural-reform public cache invalidation.
    sim.delete_arrays("uc_LCWRA_element", year)
    assert sim.calculate("uc_LCWRA_element", year)[0] == amount
    assert not calculated_by(
        sim.populations["benunit"],
        "uc_LCWRA_element",
        period(year),
        model_lcwra_element,
    )
    assert bool(sim.calculate(UC_SPECIFIED, year)[0]) == (amount > 0)

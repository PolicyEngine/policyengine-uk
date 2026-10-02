"""The benefit cap's specified-benefit exceptions follow the people the law names.

HB Regs 2006 reg 75F(1) and UC Regs 2013 reg 83(1) lift the cap where:

- the claimant or partner receives ESA that includes the support component
  (75F(1)(a); 83(1)(a)), industrial injuries benefit, attendance allowance
  or an armed forces compensation payment (75F(1)(b)-(d); 83(1)(b)-(e));
- the claimant, partner or a child or young person they are responsible for
  receives disability living allowance (75F(1)(e); 83(1)(f));
- the claimant, partner or a young person they are responsible for receives
  personal independence payment, or is entitled to Carer's Allowance or
  Carer Support Payment (75F(1)(ea), (h), (ha); 83(1)(g), (i), (ia)), or,
  for a Housing Benefit young person, armed forces independence payment
  (75F(1)(ea); UC counts it as attendance allowance, UC Regs 2013 reg 2);
- a Universal Credit claimant has limited capability for work and
  work-related activity or caring responsibilities, so the award includes the
  LCWRA or carer element (83(1)(a), (j); regs 27(1), 29(1)). A person with
  ESA of their own whose ESA lacks the support component is inferred not to
  have limited capability for work-related activity (reg 40(1)(a)(ii));
- the claimant or couple is entitled to working tax credit (HB reg 75E(2)).

The model applies one cap to both schemes, so either scheme's exception
counts. A child or young person is a child under 16, a young person in
non-advanced education, or a 16-year-old (UC reg 5(1)(a)) who does not
receive benefits in their own right (reg 5(5)) and is not looked after
(reg 4(6)).

Invariants:

1. Adding a member who is neither the claimant, the partner nor a child or
   young person they are responsible for never changes whether the family is
   exempt, its cap, its cap reduction or its Universal Credit, whatever
   disability or carer benefits, ESA, JSA, incapacity benefit, SDA,
   disability flag or caring that member has. The cap counts only the
   welfare benefits "to which the single person or couple is entitled" (UC
   Regs 2013 reg 80(1); HB Regs 2006 reg 75A). (Their age and earnings can: the State
   Pension age and earnings exceptions read every member. The draws keep the
   member under State Pension age and without earnings; see #1944, #1907,
   #1999 and #1820.)
2. The exemption equals a reference written directly from the regulations,
   with roles fixed by construction (differential test).
3. An exempt family has no cap and no reduction; any other family has the
   single cap if the claimant has no partner and no child or young person,
   and the couple-and-family cap otherwise (UC reg 80A(2); HB reg 75CA).
4. Each head alone: for every role and every circumstance, a family whose
   only circumstance is that one, held by that member, is exempt exactly when
   the reference says (an exhaustive table, for each support-component mode).

The properties draw families at random; invariant 4 enumerates them. Each
example builds many families in one simulation, in separate households
and benefit units. Roles are given explicitly (is_claimant_or_partner). The
support component is set for every person in a simulation or for none, since
an input set for some people is given its default for the rest.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, event, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2025
SINGLE_CAP, FAMILY_CAP = 14_753, 22_020  # Outside London, 2025-26.

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
def families(draw, supplied):
    """A claimant, an optional partner, up to three dependants and a
    non-dependent adult, with at most two circumstances among them."""
    members = [blank("claimant", draw(st.integers(25, 60)))]
    if draw(st.booleans()):
        members.append(blank("claimant", draw(st.integers(25, 60))))
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
    other = blank("other", draw(st.integers(17, 60)))
    for _ in range(draw(st.integers(0, 2))):
        give(draw(st.sampled_from(members)), draw(st.sampled_from(CIRCUMSTANCES)))
    for _ in range(draw(st.integers(1, 2))):
        give(other, draw(st.sampled_from(CIRCUMSTANCES)))
    if supplied:
        for person in members + [other]:
            person["esa_includes_support_component"] = draw(st.booleans())
    working_tax_credit = draw(st.sampled_from([0] * 9 + [500]))
    return members, other, working_tax_credit


@st.composite
def draws(draw):
    """Families in one simulation, sharing whether the support component is
    supplied."""
    supplied = draw(st.booleans())
    event(f"support component supplied: {supplied}")
    return draw(st.lists(families(supplied), min_size=1, max_size=6))


def situation(units, year=YEAR, extra_benunit=None):
    people, benunits, households = {}, {}, {}
    for i, (members, working_tax_credit) in enumerate(units):
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
            "working_tax_credit": {year: working_tax_credit},
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


def reference_exempt(members, working_tax_credit):
    """HB Regs 2006 regs 75E(2), 75F(1) and UC Regs 2013 reg 83(1), read
    directly, with roles known by construction."""
    claimants = [m for m in members if m["_role"] == "claimant"]
    young_persons = [m for m in members if m["_role"] in ("young_person", "sixteen")]
    hb_young_persons = [m for m in members if m["_role"] == "young_person"]
    children = [m for m in members if m["_role"] == "child"]
    # No capital, so the couple's income-related award is their reports.
    couple_award = any(m["esa_income_reported"] > 0 for m in claimants)

    def support_component(m):
        # Supplied, or assumed for anyone with their own allowance.
        return m.get("esa_includes_support_component", own_esa(m))

    def receives_esa_with_support_component(m):
        receiving = m["esa_contrib_reported"] > 0 or couple_award
        return receiving and support_component(m)

    def lcwra(m):
        # UC Regs 2013 reg 40(1)(a)(ii): an ESA award without the support
        # component means the ESA assessment found no LCWRA.
        no_support = own_esa(m) and not support_component(m)
        return m["is_disabled_for_benefits"] and not no_support

    def carer(m):
        return (
            m["care_hours"] >= 35
            or m["carers_allowance"] > 0
            or m["carer_support_payment"] > 0
        )

    def any_receives(people, benefits):
        return any(m[b] > 0 for m in people for b in benefits)

    return (
        any(receives_esa_with_support_component(m) for m in claimants)
        or any_receives(claimants, CLAIMANT_OR_PARTNER)
        or any_receives(claimants + children + young_persons, CHILD_OR_YOUNG_PERSON)
        or any_receives(claimants + young_persons, YOUNG_PERSON)
        or any_receives(claimants + hb_young_persons, HOUSING_BENEFIT_YOUNG_PERSON)
        or any(lcwra(m) for m in claimants)
        or any(carer(m) for m in claimants)
        or working_tax_credit > 0
    )


def reference_cap(members):
    # The family-rate helper counts any 16-year-old (UC reg 5(1)(a)); it does
    # not yet apply reg 5(5) to one receiving benefits in their own right.
    claimants = sum(m["_role"] == "claimant" for m in members)
    dependants = any(
        m["_role"] in ("child", "young_person", "sixteen", "sixteen_own_right")
        for m in members
    )
    return SINGLE_CAP if claimants == 1 and not dependants else FAMILY_CAP


CAPPED_FAMILY = {
    "universal_credit_pre_benefit_cap": 30_000,
    "housing_benefit_pre_benefit_cap": 0,
    "child_tax_credit": 0,
    "child_benefit": 0,
    "income_support": 0,
}


SETTINGS = settings(
    max_examples=40,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@SETTINGS
@given(draws())
def test_non_dependent_adults_never_change_the_exemption(drawn):
    without = [(members, wtc) for members, _, wtc in drawn]
    with_other = [(members + [other], wtc) for members, other, wtc in drawn]
    # 30,000 of Universal Credit before the cap; the other family-level
    # capped benefits are nil, so the capped total is UC plus whatever the
    # members' own benefits add.
    sim = Simulation(
        situation=situation(without + with_other, extra_benunit=CAPPED_FAMILY)
    )
    k = len(drawn)
    claimant_or_partner = sim.calculate("is_claimant_or_partner", YEAR)
    legacy = sim.calculate("is_child_or_young_person_for_legacy_benefits", YEAR)
    uc = sim.calculate("is_child_or_qualifying_young_person_for_universal_credit", YEAR)
    sizes = [len(members) for members, _ in without + with_other]
    starts = np.cumsum([0] + sizes[:-1])
    for i in range(k):
        # The added member is the last of its benefit unit: neither claimant,
        # partner nor anyone's dependant.
        last = starts[k + i] + sizes[k + i] - 1
        assert not (claimant_or_partner[last] or legacy[last] or uc[last]), drawn[i]
    for variable in [
        "is_benefit_cap_exempt_health_disability",
        "is_benefit_cap_exempt_other",
        "is_benefit_cap_exempt",
        "benefit_cap",
        "benefit_cap_reduction",
        "universal_credit",
    ]:
        values = sim.calculate(variable, YEAR)
        for i in range(k):
            assert values[i] == values[k + i], (variable, drawn[i])


@SETTINGS
@given(draws())
def test_exemption_matches_regulations(drawn):
    units = [(members + [other], wtc) for members, other, wtc in drawn]
    sim = Simulation(situation=situation(units))
    exempt = sim.calculate("is_benefit_cap_exempt_health_disability", YEAR)
    for i, (members, wtc) in enumerate(units):
        expected = reference_exempt(members, wtc)
        event(f"reference exempt: {expected}")
        assert exempt[i] == expected, units[i]


@SETTINGS
@given(draws())
def test_exempt_families_have_no_cap_and_others_the_statutory_cap(drawn):
    units = [(members + [other], wtc) for members, other, wtc in drawn]
    # 30,000 of Universal Credit alone exceeds either cap. The other
    # family-level capped benefits are set to nil; they only add to the excess.
    sim = Simulation(situation=situation(units, extra_benunit=CAPPED_FAMILY))
    exempt = sim.calculate("is_benefit_cap_exempt", YEAR)
    cap = sim.calculate("benefit_cap", YEAR)
    reduction = sim.calculate("benefit_cap_reduction", YEAR)
    for i, (members, _) in enumerate(units):
        if exempt[i]:
            assert np.isinf(cap[i]) and reduction[i] == 0, units[i]
        else:
            assert cap[i] == reference_cap(members), units[i]
            assert reduction[i] >= 30_000 - cap[i], units[i]


SINGLE_HEAD_ROLES = ["claimant", "partner", *sorted(ROLES), "other"]


def single_head_units(mode):
    """One family per (role, circumstance): a claimant and, unless the role is
    the claimant, one more member holding the circumstance."""
    units = []
    for role in SINGLE_HEAD_ROLES:
        for circumstance in CIRCUMSTANCES:
            claimant = blank("claimant", 40)
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
    sim = Simulation(situation=situation([(members, 0) for _, members in units]))
    exempt = sim.calculate("is_benefit_cap_exempt_health_disability", YEAR)
    mismatches = [
        (key, bool(exempt[i]))
        for i, (key, members) in enumerate(units)
        if exempt[i] != reference_exempt(members, 0)
    ]
    assert not mismatches, mismatches
    # Every role meets every circumstance, and both outcomes occur.
    assert len(units) == len(SINGLE_HEAD_ROLES) * len(CIRCUMSTANCES)
    assert exempt.any() and not exempt.all()

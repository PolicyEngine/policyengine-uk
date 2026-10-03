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

Each scheme applies its own exceptions. UC reg 83(1)(f) names a "child or
qualifying young person"; HB reg 75F(1)(e) names a "child or young person".
UC includes a 16-year-old school leaver (reg 5(1)(a)), excluding someone
receiving benefits in their own right (reg 5(5)) or looked after (reg 4(6)).
HB young persons follow Child Benefit (reg 19), so the education-based
young-person roles count in the specified-benefit reference below. UC
reg 83(1)(c) names "a claimant" for attendance allowance, which includes
AFIP (reg 2); HB reg 75F(1)(ea) also names "a young person" for AFIP.
Only UC reg 83(1)(a), (j) names the LCWRA and carer elements; only HB reg
75E(2) names entitlement to working tax credit.

Invariants:

1. Adding a member who is neither the claimant, the partner nor a child or
   young person they are responsible for never changes whether the family is
   exempt under either scheme, its caps, its reductions or its Universal Credit,
   whatever
   disability or carer benefits, ESA, JSA, incapacity benefit, SDA,
   disability flag or caring that member has. The cap counts only the
   welfare benefits "to which the single person or couple is entitled" (UC
   Regs 2013 reg 80(1); HB Regs 2006 reg 75A). The draws keep the member
   under State Pension age and without earnings: HB reg 5 reads claimant
   and partner, UC has no age exception, and the earnings exception belongs
   to UC reg 82 (see #1944, #1907, #1999 and #1820).
2. Each scheme's exemption equals its own reference written directly from
   the regulations, with roles fixed by construction (differential test).
   The old combined reference is retained as an explicit UC | HB assertion.
3. A family exempt under a scheme has no cap and no reduction to that
   scheme's award; any other family has that scheme's statutory cap
   (UC reg 80A(2); HB reg 75CA). UC reg 81 deducts the childcare element
   from the excess; HB reg 75D(2) leaves at least 50p per week.
4. Each head alone: for every role and every circumstance, a family whose
   only circumstance is that one, held by that member, is exempt exactly when
   that scheme's reference says (an exhaustive table, for each
   support-component mode).

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


def situation(units, year=YEAR, extra_benunit=None, per_benunit_inputs=None):
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
            **{
                k: {year: v}
                for k, v in (
                    per_benunit_inputs[i] if per_benunit_inputs is not None else {}
                ).items()
            },
        }
        households[f"h{i}"] = {
            "members": names,
            "region": {year: "NORTH_EAST"},
            "country": {year: "ENGLAND"},
        }
    return {"people": people, "benunits": benunits, "households": households}


def own_esa(m):
    return m["esa_contrib_reported"] > 0 or m["esa_income_reported"] > 0


def reference_specified_benefit(members, scheme):
    """UC reg 83(1) or HB reg 75F(1), with roles known by construction."""
    claimants = [m for m in members if m["_role"] == "claimant"]
    # UC reg 83 names a "qualifying young person" (reg 5); HB reg 75F
    # names a "young person" (reg 19). A school-leaver role here has no
    # Child Benefit education or terminal-date circumstance supplied.
    young_roles = ("young_person", "sixteen") if scheme == "uc" else ("young_person",)
    young_persons = [m for m in members if m["_role"] in young_roles]
    children = [m for m in members if m["_role"] == "child"]
    # No capital, so the couple's income-related award is their reports.
    couple_award = any(m["esa_income_reported"] > 0 for m in claimants)

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
        # UC reg 83(1)(c): "a claimant" receiving attendance allowance,
        # including AFIP (reg 2); HB reg 75F(1)(ea) also names "a young person".
        or any_receives(
            claimants + (young_persons if scheme == "hb" else []),
            HOUSING_BENEFIT_YOUNG_PERSON,
        )
        # Only UC reg 83(1)(a), (j): "the LCWRA element" / "the carer
        # element is included in the award of universal credit".
        or (scheme == "uc" and any(lcwra(m) for m in claimants))
        or (scheme == "uc" and any(carer(m) for m in claimants))
    )


def reference_exempt(members, working_tax_credit, scheme):
    # HB reg 75E(2): "entitled to working tax credit"; UC reg 83 has no
    # working-tax-credit exception. All constructed claimants are under SPA
    # and have no earnings, so HB reg 5 and UC reg 82 do not lift the cap.
    return reference_specified_benefit(members, scheme) or (
        scheme == "hb" and working_tax_credit > 0
    )


def reference_union(members, working_tax_credit):
    """The former shared expectation, now explicitly the union of both schemes."""
    return reference_exempt(members, working_tax_credit, "uc") or reference_exempt(
        members, working_tax_credit, "hb"
    )


def reference_cap(members, scheme):
    # The family-rate helper counts any 16-year-old (UC reg 5(1)(a)); it does
    # not yet apply reg 5(5) to one receiving benefits in their own right.
    # HB uses the same annual simplification for a school leaver's terminal
    # date (reg 19; Child Benefit regs 5 and 7). That rate approximation is
    # separate from the education-based HB specified-benefit scope above.
    claimants = sum(m["_role"] == "claimant" for m in members)
    annual_sixteen = any(
        m["_role"] != "claimant" and 16 <= m["age"] < 17 for m in members
    )
    if scheme == "uc":
        # Reg 80A(2)(c): "a single claimant ... who is not responsible
        # for a child or qualifying young person"; joint claimants use (d).
        joint_claimants = claimants == 2
        responsible_for_child_or_qyp = (
            any(m["_role"] in ("child", "young_person") for m in members)
            or annual_sixteen
        )
        single_rate = not joint_claimants and not responsible_for_child_or_qyp
    else:
        assert scheme == "hb"
        # Reg 75CA(2)(c): "single claimants"; reg 2 defines that as
        # someone who "neither has a partner nor is a lone parent".
        has_partner = claimants == 2
        lone_parent = (
            any(m["_role"] in ("child", "young_person") for m in members)
            or annual_sixteen
        )
        single_rate = not has_partner and not lone_parent
    return SINGLE_CAP if single_rate else FAMILY_CAP


CAPPED_FAMILY = {
    "universal_credit_pre_benefit_cap": 30_000,
    "housing_benefit_pre_benefit_cap": 0,
    "child_tax_credit": 0,
    "child_benefit": 0,
    "income_support": 0,
    "uc_childcare_element": 0,
}


def capped_family(scheme):
    return {
        **CAPPED_FAMILY,
        "universal_credit_pre_benefit_cap": 30_000 if scheme == "uc" else 0,
        "housing_benefit_pre_benefit_cap": 30_000 if scheme == "hb" else 0,
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
    # Give each scheme an actual 30,000 award on its own. One simulation
    # holds without-UC, with-UC, without-HB and with-HB groups, each in
    # separate households and benefit units. The other family-level capped
    # benefits are nil, so the total is the award plus claimants' own benefits.
    k = len(drawn)
    units = without + with_other
    grouped_units = units + units
    sim = Simulation(
        situation=situation(
            grouped_units,
            per_benunit_inputs=[
                capped_family(scheme) for scheme in SCHEMES for _ in units
            ],
        )
    )
    claimant_or_partner = sim.calculate("is_claimant_or_partner", YEAR)
    legacy = sim.calculate("is_child_or_young_person_for_legacy_benefits", YEAR)
    uc = sim.calculate("is_child_or_qualifying_young_person_for_universal_credit", YEAR)
    sizes = [len(members) for members, _ in grouped_units]
    starts = np.cumsum([0] + sizes[:-1])
    combined_reduction = sim.calculate("benefit_cap_reduction", YEAR)
    for group, scheme in enumerate(SCHEMES):
        offset = group * 2 * k
        group_slice = slice(offset, offset + 2 * k)
        other_scheme = "hb" if scheme == "uc" else "uc"
        assert not sim.calculate(SCHEMES[other_scheme]["reduction"], YEAR)[
            group_slice
        ].any()
        assert np.array_equal(
            combined_reduction[group_slice],
            sim.calculate(SCHEMES[scheme]["reduction"], YEAR)[group_slice],
        )
        for i in range(k):
            # The added member is the last of its benefit unit: neither claimant,
            # partner nor anyone's dependant.
            family_index = offset + k + i
            last = starts[family_index] + sizes[family_index] - 1
            assert not (claimant_or_partner[last] or legacy[last] or uc[last]), drawn[i]
    for variable in [
        *(
            variable
            for variables in SCHEMES.values()
            for variable in variables.values()
        ),
        "housing_benefit_pension_age_regulations_apply",
        "benefit_cap_welfare_benefits",
        "benefit_cap_reduction",
        "universal_credit",
        "housing_benefit",
    ]:
        values = sim.calculate(variable, YEAR)
        for group, scheme in enumerate(SCHEMES):
            offset = group * 2 * k
            for i in range(k):
                assert values[offset + i] == values[offset + k + i], (
                    scheme,
                    variable,
                    drawn[i],
                )


@SETTINGS
@given(draws())
def test_exemption_matches_regulations(drawn):
    units = [(members + [other], wtc) for members, other, wtc in drawn]
    sim = Simulation(situation=situation(units))
    overall = {}
    for scheme, variables in SCHEMES.items():
        specified = sim.calculate(variables["specified"], YEAR)
        overall[scheme] = sim.calculate(variables["exempt"], YEAR)
        for i, (members, wtc) in enumerate(units):
            expected = reference_specified_benefit(members, scheme)
            event(f"{scheme} reference specified-benefit exempt: {expected}")
            assert specified[i] == expected, (scheme, units[i])
            assert overall[scheme][i] == reference_exempt(members, wtc, scheme), (
                scheme,
                units[i],
            )
    # Keep the old shared property explicitly as UC | HB, including HB 75E.
    union = overall["uc"] | overall["hb"]
    for i, (members, wtc) in enumerate(units):
        assert union[i] == reference_union(members, wtc), units[i]


@SETTINGS
@given(draws())
def test_exempt_families_have_no_cap_and_others_the_statutory_cap(drawn):
    units = [(members + [other], wtc) for members, other, wtc in drawn]
    # Each scheme receives 30,000 on its own, so its award exceeds either
    # statutory cap. Separate UC and HB family groups share one simulation,
    # with the other award nil in every benefit unit.
    k = len(units)
    sim = Simulation(
        situation=situation(
            units + units,
            per_benunit_inputs=[
                capped_family(scheme) for scheme in SCHEMES for _ in units
            ],
        )
    )
    totals = sim.calculate("benefit_cap_welfare_benefits", YEAR)
    combined_reductions = sim.calculate("benefit_cap_reduction", YEAR)
    for group, (scheme, variables) in enumerate(SCHEMES.items()):
        group_slice = slice(group * k, (group + 1) * k)
        exempt = sim.calculate(variables["exempt"], YEAR)[group_slice]
        cap = sim.calculate(variables["cap"], YEAR)[group_slice]
        reduction = sim.calculate(variables["reduction"], YEAR)[group_slice]
        total = totals[group_slice]
        combined_reduction = combined_reductions[group_slice]
        other_scheme = "hb" if scheme == "uc" else "uc"
        assert not sim.calculate(SCHEMES[other_scheme]["reduction"], YEAR)[
            group_slice
        ].any()
        assert np.array_equal(combined_reduction, reduction)
        for i, (members, _) in enumerate(units):
            if exempt[i]:
                assert np.isinf(cap[i]) and reduction[i] == 0, (scheme, units[i])
            else:
                assert cap[i] == reference_cap(members, scheme), (scheme, units[i])
                excess = max(total[i] - cap[i], 0)
                # UC reg 81: excess - childcare (0 here); HB reg 75D(2):
                # min(excess, award - 0.50 * 52) = min(excess, 29,974).
                expected = excess if scheme == "uc" else min(excess, 30_000 - 26)
                assert reduction[i] == expected, (scheme, units[i])
                assert reduction[i] >= 30_000 - cap[i], (scheme, units[i])


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
    exemptions = {}
    for scheme, variables in SCHEMES.items():
        exempt = sim.calculate(variables["specified"], YEAR)
        exemptions[scheme] = exempt
        mismatches = [
            (scheme, key, bool(exempt[i]))
            for i, (key, members) in enumerate(units)
            if exempt[i] != reference_specified_benefit(members, scheme)
        ]
        assert not mismatches, mismatches
        assert exempt.any() and not exempt.all()
    union = exemptions["uc"] | exemptions["hb"]
    mismatches = [
        (key, bool(union[i]))
        for i, (key, members) in enumerate(units)
        if union[i] != reference_union(members, 0)
    ]
    assert not mismatches, mismatches
    # Every role meets every circumstance under each scheme.
    assert len(units) == len(SINGLE_HEAD_ROLES) * len(CIRCUMSTANCES)

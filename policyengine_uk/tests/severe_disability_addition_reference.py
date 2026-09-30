"""Independent reference: Pension Credit severe disability additional amount.

Test oracle for test_severe_disability_addition_properties.py. It was written
from the law text and a written specification by a separate agent that did not
see the implementation under test; the only later edit is rule 3 (which unit's
claimant or partner a carer in another benefit unit is treated as caring for),
marked below.

State Pension Credit Regulations 2002 (SI 2002/1792):
  * regulation 6(4) and 6(5)                      (law/spc_reg6.txt)
  * Schedule I, Part I, paragraph 1(1)(a)-(c)      (law/spc_sch1_p1.txt)
  * Schedule I, Part I, paragraph 2                (law/spc_sch1_p2.txt)
  * Schedule I, Part I, paragraph 3                (law/spc_sch1_p3.txt)

Written from the law text and the differential-test spec only. It does not
import or read the PolicyEngine implementation under test.

``reference_rates(household)`` returns, for every benefit unit, the number of
single-rate severe disability additional amounts: 0, 1 (reg 6(5)(a), £86.05)
or 2 (reg 6(5)(b), £172.10).

Input format::

    household = {
        "benunits": {bu_id: {"claimant_or_partner": [pid, ...],
                             "others": [pid, ...]}},
        "people": {pid: {"age": int,
                         "qualifying_benefit": bool,
                         "blind": bool,
                         "qualifying_young_person": bool,
                         "receives_carer_benefit": bool}},
    }

A unit with two ``claimant_or_partner`` entries is a couple; with one, a single
claimant. ``others`` are unit members who are neither claimant nor partner.

Modelling rules (from the spec; each is applied literally below):

1. Qualifying benefit. A person satisfies para 1(1)(a)(i), (b)(i) and (c)(i)
   iff ``qualifying_benefit``.
2. Residence. Para 1(1)(a)(ii), (b)(ii) and (c)(iii) fail if anyone in the
   household other than this unit's claimant/partner is aged 18 or over and is
   not a para 2 person. Modelled para 2 persons: qualifying benefit (2(2)(a)),
   blind (2(2)(b)), qualifying young person (2(2)(f)). No other exceptions.
3. Carers. Nobody cares for themselves. A claimant/partner who receives a carer
   benefit cares for their partner if the partner qualifies; otherwise they care
   for someone outside the unit. Any other member of a unit who receives a carer
   benefit cares for a qualifying claimant/partner of their own unit if it has
   one. Every remaining carer in the household (one not caring within their own
   unit) cares for a qualifying claimant/partner of THIS unit. Each such carer
   cares for a different qualifying person who is not already cared for, until
   every qualifying claimant/partner is cared for.
4. Heads. Para 1(1)(a) applies to singles; (b) and then (c) apply to couples.
   (c) applies only where (b) does not, and (c)(iv) needs no carer for the
   partner to whom (c)(i) applies. If both partners qualify, either may be the
   (c)(i) person, and the other must be blind. Then reg 6(5): 2 if (b) is
   satisfied and nobody cares for either partner; otherwise 1 if any of (a),
   (b) or (c) is satisfied; otherwise 0.

Not modelled (outside the spec): reg 6(2)-(3) prisoners and members of
religious orders; para 1(2) deemed receipt (backdated awards, payments in lieu,
hospital patients, carer benefit before first payment); para 1(3) 28-week run-on
for regained sight; para 2(2)(c), (d), (e), 2(3)-(7); para 3 (what counts as
"residing with"). Everyone in ``people`` counts as normally residing with every
benefit unit in the household.
"""

from __future__ import annotations

from itertools import combinations
from typing import Any, Hashable, Mapping, Sequence

Person = Mapping[str, Any]
PersonId = Hashable

# Sch I para 1(1)(a)(ii), (b)(ii), (c)(iii): "no person who has attained the age of 18".
# A person "has attained the age of 18" on their 18th birthday, so the test is age >= 18.
ADULT_AGE = 18


# ---------------------------------------------------------------------------
# Rule 1: the qualifying disability benefit
# ---------------------------------------------------------------------------


def qualifies(person: Person) -> bool:
    """Sch I para 1(1)(a)(i), (b)(i) and (c)(i): receipt of a qualifying benefit.

    Law, para 1(1)(a)(i): "he is in receipt of attendance allowance , pension age
    disability payment , the care component of disability living allowance at the
    highest or middle rate [...] the daily living component of personal
    independence payment at the standard or enhanced rate [...] or armed forces
    independence payment".

    (b)(i) asks that "both partners are in receipt of" the same list and (c)(i)
    that "either the claimant or his partner is in receipt of" it.

    Spec rule 1: a person qualifies iff ``qualifying_benefit``.
    """
    return bool(person["qualifying_benefit"])


# ---------------------------------------------------------------------------
# Rule 2: the residence (non-dependant) condition
# ---------------------------------------------------------------------------


def is_paragraph_2_person(person: Person) -> bool:
    """Sch I para 2: residents whose presence is ignored for the residence test.

    Law, para 2(1): "For the purposes of paragraph 1(1)(a)(ii), (b)(ii) and
    (c)(iii), this paragraph applies to the persons specified in the following
    sub-paragraphs."

    Modelled heads of para 2(2), "A person who--":
      (a) "is in receipt of attendance allowance , pension age disability payment ,
          the care component of disability living allowance at the highest or middle
          rate [...] or armed forces independence payment;"  -> qualifying_benefit
      (b) "is certified as severely sight impaired or blind by a consultant
          ophthalmologist;"                                   -> blind
      (f) "is a person who is a qualifying young person within the meaning of
          regulation 4A or child as defined in section 40 of the 2012 Act."
                                                              -> qualifying_young_person
          (A section 40 "child" is under 16, so the age test already ignores
          them.)

    Spec rule 2: no other exceptions. 2(2)(c)-(e) and 2(3)-(7) are not modelled.
    """
    return bool(
        person["qualifying_benefit"]  # para 2(2)(a)
        or person["blind"]  # para 2(2)(b)
        or person["qualifying_young_person"]  # para 2(2)(f)
    )


def is_disqualifying_resident(person: Person) -> bool:
    """A resident who breaks the residence condition.

    Law, para 1(1)(a)(ii): "no person who has attained the age of 18 is normally
    residing with the claimant, nor is the claimant normally residing with such a
    person, other than a person to whom paragraph 2 applies".
    """
    return person["age"] >= ADULT_AGE and not is_paragraph_2_person(person)


def residence_condition_met(
    people: Mapping[PersonId, Person],
    claimant_or_partner: Sequence[PersonId],
) -> bool:
    """Sch I para 1(1)(a)(ii) (single), (b)(ii) first limb and (c)(iii) (couple).

    Law, para 1(1)(a)(ii): "no person who has attained the age of 18 is normally
    residing with the claimant, nor is the claimant normally residing with such a
    person, other than a person to whom paragraph 2 applies".

    Law, para 1(1)(b)(ii) and (c)(iii): "no person who has attained the age of 18
    is normally residing with the partners, nor are the partners normally residing
    with such a person, other than a person to whom paragraph 2 applies".

    Spec rule 2: everyone in the household except this unit's claimant/partner is
    tested. That covers "others" in this unit and every member of any other unit.
    A partner is never "residing with the partners" in this sense, so an adult
    partner without a qualifying benefit does not break the condition.
    """
    own = set(claimant_or_partner)
    return not any(
        is_disqualifying_resident(person)
        for pid, person in people.items()
        if pid not in own
    )


# ---------------------------------------------------------------------------
# Rule 3: who is cared for (carer's allowance, carer support payment, UC carer element)
# ---------------------------------------------------------------------------


def _cares_within_other_unit(people, units, pid, unit_id) -> bool:
    """[Rule 3 as amended] Whether ``pid``, a member of a unit other than
    ``unit_id``, cares for a qualifying claimant or partner of their own unit."""
    for other_id, other in units.items():
        if other_id == unit_id:
            continue
        members = list(other["claimant_or_partner"]) + list(other.get("others", []))
        if pid not in members:
            continue
        return any(
            qualifies(people[q]) for q in other["claimant_or_partner"] if q != pid
        )
    return False


def carer_assignments(
    people: Mapping[PersonId, Person],
    claimant_or_partner: Sequence[PersonId],
    units: Mapping[Hashable, Any] = None,
    unit_id: Hashable = None,
) -> list[frozenset]:
    """Every allowed set of this unit's claimant/partners who are cared for.

    The carer conditions are para 1(1)(a)(iii), (b)(ii) second limb, (c)(iv) and
    reg 6(5)(b). Each asks whether a person "is entitled to and in receipt of an
    allowance under section 70 of the 1992 Act (carer's allowance) or carer support
    payment , or has an award of universal credit which includes the carer
    element, in respect of caring for" a named person.

    Spec rule 3:
      * Nobody cares for themselves.
      * A claimant/partner who receives a carer benefit cares for their partner if
        the partner qualifies; otherwise they care for someone outside the unit.
      * Every other household member (an "other" in this unit or anyone in another
        unit) who receives a carer benefit cares for a qualifying claimant/partner
        of THIS unit. Each cares for a different qualifying person who is not
        already cared for, until every qualifying claimant/partner is cared for.

    Rule 3 does not say which partner an outside carer takes when both qualify and
    neither is yet cared for. This function returns every allowed assignment, and
    ``reference_rates`` asserts that the answer is the same for all of them.
    """
    units = units or {}
    unit = list(claimant_or_partner)
    qualifying = [pid for pid in unit if qualifies(people[pid])]

    # Partner carers: A cares for B only when B qualifies. A claimant/partner is
    # never their own carer, and in a single unit has no partner to care for.
    cared_by_partner = set()
    if len(unit) == 2:
        first, second = unit
        for carer, cared in ((first, second), (second, first)):
            if people[carer]["receives_carer_benefit"] and qualifies(people[cared]):
                cared_by_partner.add(cared)

    # Outside carers: every household member who is not this unit's claimant or
    # partner and who is not caring within their own (other) unit. [Rule 3 as
    # amended: a carer in another unit cares there if that unit has a
    # qualifying claimant or partner other than the carer.]
    own = set(unit)
    outside_carers = sum(
        1
        for pid, person in people.items()
        if pid not in own
        and person["receives_carer_benefit"]
        and not _cares_within_other_unit(people, units, pid, unit_id)
    )

    still_uncared = [pid for pid in qualifying if pid not in cared_by_partner]
    newly_cared = min(outside_carers, len(still_uncared))
    return [
        frozenset(cared_by_partner) | frozenset(choice)
        for choice in combinations(still_uncared, newly_cared)
    ]


# ---------------------------------------------------------------------------
# Rule 4: the three heads of para 1(1) and reg 6(5)
# ---------------------------------------------------------------------------


def head_a_satisfied(
    people: Mapping[PersonId, Person],
    claimant: PersonId,
    residence_ok: bool,
    cared_for: frozenset,
) -> bool:
    """Sch I para 1(1)(a): "in the case of a claimant who has no partner--"

    (i)   "he is in receipt of attendance allowance , [...] or armed forces
          independence payment; and"
    (ii)  "no person who has attained the age of 18 is normally residing with the
          claimant, [...] other than a person to whom paragraph 2 applies; and"
    (iii) "no person is entitled to and in receipt of an allowance under section 70
          of the 1992 Act (carer's allowance) or carer support payment , or has an
          award of universal credit which includes the carer element, in respect of
          caring for him;"
    """
    return (
        qualifies(people[claimant])  # (a)(i)
        and residence_ok  # (a)(ii)
        and claimant not in cared_for  # (a)(iii)
    )


def head_b_satisfied(
    people: Mapping[PersonId, Person],
    partners: Sequence[PersonId],
    residence_ok: bool,
    cared_for: frozenset,
) -> bool:
    """Sch I para 1(1)(b): "in the case of a claimant who has a partner--"

      (i)   "both partners are in receipt of attendance allowance , [...] or armed
            forces independence payment; and"
      (ii)  "no person who has attained the age of 18 is normally residing with the
            partners, [...] other than a person to whom paragraph 2 applies; and
            either a person is entitled to, and in receipt of, an allowance under
            section 70 of the 1992 Act or carer support payment , or has an award of
            universal credit which includes the carer element, in respect of caring
            for one only of the partners or, as the case may be, no person is
            entitled to, and in receipt of, such an allowance [...] in respect of
            caring for either partner;"

    The carer limb of (b)(ii) holds when zero or one partner is cared for. It
    fails only when both are.
    """
    both_qualify = all(qualifies(people[pid]) for pid in partners)  # (b)(i)
    partners_cared_for = sum(1 for pid in partners if pid in cared_for)
    carer_limb = partners_cared_for <= 1  # (b)(ii): "one only" or "either" (none)
    return both_qualify and residence_ok and carer_limb


def head_c_satisfied(
    people: Mapping[PersonId, Person],
    partners: Sequence[PersonId],
    residence_ok: bool,
    cared_for: frozenset,
) -> bool:
    """Sch I para 1(1)(c): "in the case of a claimant who has a partner and to whom
    head (b) does not apply--"

      (i)   "either the claimant or his partner is in receipt of attendance
            allowance , [...] or armed forces independence payment; and"
      (ii)  "the other partner is certified as severely sight impaired or blind by a
            consultant ophthalmologist; and"
      (iii) "no person who has attained the age of 18 is normally residing with the
            partners, [...] other than a person to whom paragraph 2 applies; and"
      (iv)  "no person is entitled to and in receipt of an allowance under section 70
            of the 1992 Act or carer support payment , or has an award of universal
            credit which includes the carer element, in respect of caring for the
            person to whom head (c) (i) above applies."

    The caller checks "to whom head (b) does not apply". Where both partners
    qualify, either may be the (c)(i) person (spec rule 4), so (c) holds if any
    ordered choice works.
    """
    first, second = partners
    for c_i_person, other_partner in ((first, second), (second, first)):
        if (
            qualifies(people[c_i_person])  # (c)(i)
            and people[other_partner]["blind"]  # (c)(ii)
            and residence_ok  # (c)(iii)
            and c_i_person not in cared_for  # (c)(iv)
        ):
            return True
    return False


def rates_for_unit(
    people: Mapping[PersonId, Person],
    claimant_or_partner: Sequence[PersonId],
    cared_for: frozenset,
) -> int:
    """Reg 6(4) and 6(5) for one benefit unit and one carer assignment.

    Law, reg 6(4): "Except in a case to which paragraph (3) applies, an amount
    additional to that prescribed in paragraph (1) shall be applicable under
    paragraph (5) if the claimant is treated as being a severely disabled person in
    accordance with paragraph 1 of Part I of Schedule I."

    Law, reg 6(5): "The additional amount applicable is--
      (a) except where paragraph (b) applies, £86.05 per week if paragraph 1(1)(a),
          (b) or (c) of Part I of Schedule I is satisfied; or
      (b) £172.10 per week if paragraph 1(1)(b) of Part I of Schedule I is satisfied
          otherwise than by virtue of paragraph 1(2)(b) of that Part and no one is
          entitled to and in receipt of an allowance under section 70 of the 1992
          Act or carer support payment , or has an award of universal credit which
          includes the carer element under regulation 29 of the Universal Credit
          Regulations 2013, in respect of caring for either partner."

    The 1(2)(b) proviso (hospital patients deemed in receipt) is outside the model:
    ``qualifying_benefit`` means actual receipt, so the proviso always holds. Reg
    6(3) (prisoners, religious orders) is not modelled either.
    """
    residence_ok = residence_condition_met(people, claimant_or_partner)

    if len(claimant_or_partner) == 1:
        (claimant,) = claimant_or_partner
        return 1 if head_a_satisfied(people, claimant, residence_ok, cared_for) else 0

    partners = list(claimant_or_partner)
    b = head_b_satisfied(people, partners, residence_ok, cared_for)
    # (c) applies only "to whom head (b) does not apply".
    c = (not b) and head_c_satisfied(people, partners, residence_ok, cared_for)
    nobody_cares_for_either = not any(pid in cared_for for pid in partners)
    if b and nobody_cares_for_either:
        return 2  # reg 6(5)(b)
    if b or c:
        return 1  # reg 6(5)(a)
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


_PERSON_FIELDS = (
    "age",
    "qualifying_benefit",
    "blind",
    "qualifying_young_person",
    "receives_carer_benefit",
)


def _validate(household: Mapping[str, Any]) -> None:
    people = household["people"]
    seen: dict = {}
    for bu_id, unit in household["benunits"].items():
        cp = list(unit["claimant_or_partner"])
        if len(cp) not in (1, 2):
            raise ValueError(
                f"benefit unit {bu_id!r} needs 1 or 2 claimant_or_partner, got {len(cp)}"
            )
        for pid in cp + list(unit.get("others", [])):
            if pid not in people:
                raise ValueError(f"benefit unit {bu_id!r} names unknown person {pid!r}")
            if pid in seen:
                raise ValueError(
                    f"person {pid!r} appears in benefit units {seen[pid]!r} and {bu_id!r}"
                )
            seen[pid] = bu_id
    for pid, person in people.items():
        missing = [f for f in _PERSON_FIELDS if f not in person]
        if missing:
            raise ValueError(f"person {pid!r} is missing {missing}")


def reference_rates(household: Mapping[str, Any]) -> dict:
    """Number of single-rate SDA amounts (0, 1 or 2) for every benefit unit.

    The household is everyone in ``household["people"]``. Each benefit unit is
    tested against every other member of the household (spec rules 2 and 3).
    """
    _validate(household)
    people = household["people"]
    result = {}
    for bu_id, unit in household["benunits"].items():
        claimant_or_partner = list(unit["claimant_or_partner"])
        outcomes = {
            rates_for_unit(people, claimant_or_partner, cared_for)
            for cared_for in carer_assignments(
                people, claimant_or_partner, household["benunits"], bu_id
            )
        }
        # Rule 3 leaves open which qualifying partner an outside carer takes. The
        # law makes that choice immaterial: (b) depends only on how many partners
        # are cared for; (c) can be reached with the residence condition met only
        # when both partners are cared for, and then (c)(iv) fails for either choice.
        # Fail loudly if that reasoning is ever wrong.
        if len(outcomes) != 1:
            raise AssertionError(
                f"benefit unit {bu_id!r}: result depends on carer assignment: {outcomes}"
            )
        result[bu_id] = outcomes.pop()
    return result

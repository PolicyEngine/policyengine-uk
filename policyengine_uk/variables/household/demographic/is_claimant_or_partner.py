from policyengine_uk.model_api import *


class is_claimant_or_partner(Variable):
    """The single adult or couple a benefit unit is formed around.

    In benefit law this is the claimant and their partner, as opposed to the
    children and young persons they are responsible for (SSCBA 1992 s.137(1)
    "family"; WRA 2012 ss.39-40; SPCA 2002 s.17; TCA 2002 s.3). The same two
    people are the spouses or civil partners for income tax purposes when the
    benefit unit is a married couple. A benefit unit has one claimant, or a
    couple: never more than two.

    Datasets or users can supply this directly. Otherwise it is inferred from
    benefit-unit structure, which follows the Family Resources Survey: a single
    adult or a couple plus dependent children.

    - Only HBAI adults (`is_hbai_adult`) can be a claimant or partner.
    - The claimant is the benefit-unit head (the eldest adult head if more
      than one is given), or the eldest adult if the head is not an adult.
    - The partner is one other member: the eldest other member flagged as a
      parent (`is_parent`) if there is one, otherwise the eldest other adult
      who is not presumed to be the claimant's child. A member at least 16
      years younger than the claimant is presumed to be their child if they
      are under 20 or the claimant is flagged as a parent, and a member at
      least 20 years younger is presumed their child at any age (PolicyEngine
      presumptions for households entered without relationships). So a lone
      parent flagged `is_parent` who is the claimant and lives with an
      unflagged son or daughter at least 16 years younger is single, and the
      son or daughter is neither claimant nor partner.
    - Without any parent flag, a member aged 20 or over is presumed a child
      only when at least 20 years younger. In the Family Resources Survey,
      co-resident adults 20 or more years apart are mostly in separate benefit
      units, while those 16 to 19 years apart are mostly couples. A couple 20
      or more years apart entered without flags or roles is therefore assessed
      as a single claimant; supply `is_claimant_or_partner` for such a couple.
      Survey datasets can supply it from the survey's own benefit units.
    - Flags follow the Family Resources Survey convention: in a benefit unit
      with children, both members of the couple are flagged as parents. If
      only the claimant of a couple with children is flagged, a partner 16 or
      more years younger is presumed to be their child, and the couple is
      assessed as a lone parent. When relationships are known, supply this
      variable for everyone (true for the claimant and any partner, false for
      everyone else) rather than relying on the presumption.
    - If the claimant is not flagged as a parent but two or more other members
      are, the two eldest of those are the claimant and partner instead (for
      example parents living in a grandparent's benefit unit).
    - Any further adults are neither claimant nor partner.
    """

    value_type = bool
    entity = Person
    label = "Claimant or partner"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/137",
        "https://www.legislation.gov.uk/ukpga/2012/5/section/39",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/17",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
    )

    def formula(person, period, parameters):
        p = parameters(period).household.demographic.benefit_unit.presumed_child
        age = person("age", period)
        adult = person("is_hbai_adult", period)
        is_head = person("is_benunit_head", period)
        head_is_adult = person.benunit.any(is_head & adult)
        eldest_adult = adult & (
            person.get_rank(person.benunit, -age, condition=adult) == 0
        )
        # With more than one head (malformed input), the eldest adult head.
        adult_head = is_head & adult
        eldest_adult_head = adult_head & (
            person.get_rank(person.benunit, -age, condition=adult_head) == 0
        )
        claimant = where(head_is_adult, eldest_adult_head, eldest_adult)
        claimant_age = person.benunit.max(where(claimant, age, -np.inf))
        identified_parent = adult & person("is_parent", period)
        other_parent = identified_parent & ~claimant
        claimant_is_parent = person.benunit.any(claimant & identified_parent)
        # Two flagged parents other than a non-parent claimant are the couple.
        parents_are_couple = (person.benunit.sum(other_parent) >= 2) & ~(
            claimant_is_parent
        )
        parent_couple = other_parent & (
            person.get_rank(person.benunit, -age, condition=other_parent) < 2
        )
        # Below a flagged parent the age limit does not apply: a much younger
        # unflagged member is their child, whatever their age. Without flags,
        # only a larger gap overrides the age limit.
        gap = claimant_age - age
        presumed_child = (
            ((age < p.age_limit) | claimant_is_parent) & (gap >= p.minimum_age_gap)
        ) | (gap >= p.minimum_age_gap_at_any_age)
        other_adult = adult & ~claimant & ~presumed_child
        pool = where(person.benunit.any(other_parent), other_parent, other_adult)
        partner = pool & (person.get_rank(person.benunit, -age, condition=pool) == 0)
        return where(parents_are_couple, parent_couple, claimant | partner)

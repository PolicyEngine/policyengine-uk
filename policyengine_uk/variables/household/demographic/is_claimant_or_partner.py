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
    - The benefit-unit head is the claimant.
    - The partner is one other member: the eldest member flagged as a parent
      (`is_parent`) if there is one, otherwise the eldest other adult who is
      not presumed to be the head's child. A member under 20 and at least 16
      years younger than the head is presumed to be their child (a PolicyEngine
      presumption for households entered without relationships). Any further
      adults are neither claimant nor partner.
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
        head_age = person.benunit.max(where(is_head, age, -np.inf))
        presumed_child_of_head = (age < p.age_limit) & (
            head_age - age >= p.minimum_age_gap
        )
        identified_partner = adult & ~is_head & person("is_parent", period)
        other_adult = adult & ~is_head & ~presumed_child_of_head
        pool = where(
            person.benunit.any(identified_partner), identified_partner, other_adult
        )
        partner = pool & (person.get_rank(person.benunit, -age, condition=pool) == 0)
        return (is_head & adult) | partner

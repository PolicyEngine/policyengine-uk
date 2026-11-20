from policyengine_uk.model_api import *
from policyengine_uk.variables.household.consumption.rent.non_dependant_normally_resides_with import (
    non_dependants_residing_with,
)


class housing_benefit_has_non_dependant(Variable):
    value_type = bool
    entity = BenUnit
    label = "Has a non-dependant residing with them (Housing Benefit)"
    documentation = (
        "Someone in this benefit unit who is neither a claimant or partner "
        "nor a child or young person (including one placed with the family "
        "as a foster child or for adoption), or, for a family liable for the "
        "household's rent (the household head's or a sharer's), anyone in "
        "the household who is a non-dependant (see "
        "is_non_dependant_of_household_head) and normally resides with it. "
        "Where the rent is shared, a non-dependant resides with each joint "
        "occupier that non_dependant_normally_resides_with gives, by default "
        "every one; a joint occupier's own family is never another's "
        "non-dependant, whatever its rent. A boarder's or lodger's family "
        "has none from the householder's household."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/21",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://assets.publishing.service.gov.uk/media/5a758238ed915d6faf2b38a2/lha-guidance-manual.pdf#page=33",
    )

    def formula(benunit, period, parameters):
        # HB Regs 2006 reg 3(1)-(2), (4) and reg 74(5).
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        age = person("age", period)
        # Reg 3(2)(c): a child or young person living with the claimant who
        # is not a member of the household by virtue of reg 21, such as one
        # placed with the claimant or partner as a foster child or for
        # adoption (reg 21(3)), is not a non-dependant.
        child_or_young_person = (
            person("is_child_or_young_person_for_legacy_benefits", period)
            | person("is_child_or_young_person_placed_with_family", period)
            | ((age >= 16) & (age < 17))
        )
        within_benefit_unit = benunit.any(~claimant_or_partner & ~child_or_young_person)
        liable_family = benunit.any(person("is_liable_for_household_rent", period))
        # Reg 3(1), (2)(d) and (4): a non-dependant of several joint
        # occupiers resides with each of them (LHA Guidance Manual paras
        # 2.050 and 2.110); one who lives with one joint tenant only resides
        # with that tenant alone (para 2.093, example 2). A member of a joint
        # occupier's family is no one's non-dependant, even where the family
        # has no rent of its own.
        non_dependants = non_dependants_residing_with(
            benunit, period, person("is_non_dependant_of_household_head", period)
        )
        return within_benefit_unit | (liable_family & (non_dependants > 0))

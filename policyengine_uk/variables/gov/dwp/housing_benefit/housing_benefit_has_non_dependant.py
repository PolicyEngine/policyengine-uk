from policyengine_uk.model_api import *


class housing_benefit_has_non_dependant(Variable):
    value_type = bool
    entity = BenUnit
    label = "Has a non-dependant residing with them (Housing Benefit)"
    documentation = (
        "Someone in this benefit unit who is neither a claimant or partner "
        "nor a child or young person, or, for a family liable for the "
        "household's rent (the household head's or a sharer's), anyone in "
        "the household who is a non-dependant (see "
        "is_non_dependant_of_household_head). A non-dependant normally "
        "residing in the dwelling resides with each joint occupier. A "
        "boarder's or lodger's family has none from the householder's "
        "household."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
    )

    def formula(benunit, period, parameters):
        # HB Regs 2006 reg 3(1)-(2), (4) and reg 74(5).
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        age = person("age", period)
        child_or_young_person = person(
            "is_child_or_young_person_for_legacy_benefits", period
        ) | ((age >= 16) & (age < 17))
        within_benefit_unit = benunit.any(~claimant_or_partner & ~child_or_young_person)
        liable_family = benunit.any(person("is_liable_for_household_rent", period))
        non_dependants = benunit.max(
            person.household.sum(person("is_non_dependant_of_household_head", period))
        )
        return within_benefit_unit | (liable_family & (non_dependants > 0))

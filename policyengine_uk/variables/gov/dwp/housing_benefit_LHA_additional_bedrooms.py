from policyengine_uk.model_api import *


class housing_benefit_LHA_additional_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "Additional bedrooms in the Housing Benefit size criteria"
    documentation = (
        "One additional bedroom if the claimant, partner, another occupier "
        "or a child placed with the claimant needs overnight care (see "
        "meets_lha_overnight_care_condition), and one if the claimant or "
        "partner is a qualifying parent or carer (see "
        "is_housing_benefit_qualifying_parent_or_carer): two if both. "
        "Occupiers outside the family count for the household head's family: "
        "non-dependants, boarders and lodgers and their children, but not a "
        "sharer of the rent or a child placed with them as a foster child or "
        "for adoption. The definitions require a bedroom in the dwelling for "
        "the carer or the foster child; the model does not observe the "
        "dwelling's bedrooms and assumes there is one. Children and couples "
        "who cannot share a bedroom because of disability are not modelled."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        overnight_care = person("meets_lha_overnight_care_condition", period)
        # HB Regs 2006 reg 13D(3A)(a)(iii) and 13D(12): occupiers of other
        # families, other than a joint tenant outside the claimant's
        # household and a child placed with another family as a foster child
        # or for adoption (see housing_benefit_LHA_allowed_bedrooms).
        head_family = person.benunit.any(person("is_household_head", period))
        sharer = person.benunit("liable_for_share_of_household_rent", period)
        placed = person("is_child_or_young_person_placed_with_family", period)
        other = overnight_care & ~head_family & ~sharer & ~placed
        is_head_family = benunit.any(person("is_household_head", period))
        others = is_head_family * benunit.max(person.household.sum(other))
        # Reg 13D(3A)(a)(i)-(iv): the claimant, partner, other members of the
        # family, and a child or young person for whom the claimant or
        # partner is a qualifying parent or carer.
        overnight_room = benunit.any(overnight_care) | (others > 0)
        # Reg 13D(3A)(b).
        carer_room = benunit("is_housing_benefit_qualifying_parent_or_carer", period)
        # Reg 13D(3B): two additional bedrooms where both apply.
        return 1.0 * overnight_room + 1.0 * carer_room

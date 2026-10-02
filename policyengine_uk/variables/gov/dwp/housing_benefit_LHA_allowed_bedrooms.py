from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_allowed_bedrooms import (
    bedrooms_for_children,
)


class housing_benefit_LHA_allowed_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "Bedrooms in the Housing Benefit size criteria"
    documentation = (
        "Housing Benefit size criteria: one bedroom for the claimant or "
        "couple, one for each other occupier aged 16 or over (an occupier "
        "couple sharing one), and the children's bedrooms. Occupiers are "
        "everyone who lives in the dwelling as their home except a joint "
        "tenant outside the claimant's household. So every member of the benefit unit aged 16 or over who "
        "is not the claimant or partner adds a bedroom, such as a young "
        "person in full-time education; so do a householder's boarder or "
        "lodger and a non-dependant, but a sharer of the rent does not. A "
        "sharer's, boarder's or lodger's own claim counts only their own "
        "family."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/2",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # A child is a person under 16 (HB Regs 2006 reg 2(1)).
        aged_16_or_over = person("age", period) >= 16
        # HB Regs 2006 reg 13D(3)(b): a person who is not a child, here a
        # member of the benefit unit other than the claimant or partner.
        claimant_or_partner = person("is_claimant_or_partner", period)
        family_rooms = benunit.sum(aged_16_or_over & ~claimant_or_partner)
        head_family = person.benunit.any(person("is_household_head", period))
        sharer = person.benunit("liable_for_share_of_household_rent", period)
        # Reg 13D(3) for occupiers outside the family, as defined in 13D(12):
        # a couple has one bedroom ((a)) and anyone else aged 16 or over one
        # each ((b)), so each member of a couple counts as half. The extra
        # bedroom for a couple who cannot share ((za)) is not modelled.
        in_couple = claimant_or_partner & (
            person.benunit.sum(claimant_or_partner & aged_16_or_over) == 2
        )
        other_occupier = (aged_16_or_over & ~head_family & ~sharer) * where(
            in_couple, 0.5, 1
        )
        is_head_family = benunit.any(person("is_household_head", period))
        other_occupiers = is_head_family * benunit.max(
            person.household.sum(other_occupier)
        )
        return (
            1 + family_rooms + other_occupiers + bedrooms_for_children(benunit, period)
        )

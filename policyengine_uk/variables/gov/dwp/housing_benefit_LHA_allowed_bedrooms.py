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
        "couple, one for each other occupier aged 16 or over, and the "
        "children's bedrooms. Occupiers are everyone who lives in the "
        "dwelling as their home except a joint tenant outside the claimant's "
        "household, so a householder's boarder or lodger adds a bedroom, as "
        "does a non-dependant, but a sharer of the rent does not. A sharer's, "
        "boarder's or lodger's own claim counts only their own family."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/13D",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        aged_16_or_over = person("age", period) >= 16
        head_family = person.benunit.any(person("is_household_head", period))
        sharer = person.benunit("liable_for_share_of_household_rent", period)
        # HB Regs 2006 reg 13D(3), with "occupiers" as defined in 13D(12).
        other_occupier = aged_16_or_over & ~head_family & ~sharer
        is_head_family = benunit.any(person("is_household_head", period))
        other_occupiers = is_head_family * benunit.max(
            person.household.sum(other_occupier)
        )
        return 1 + other_occupiers + bedrooms_for_children(benunit, period)

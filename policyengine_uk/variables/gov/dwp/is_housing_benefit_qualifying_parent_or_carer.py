from policyengine_uk.model_api import *


class is_housing_benefit_qualifying_parent_or_carer(Variable):
    value_type = bool
    entity = BenUnit
    label = "Housing Benefit claimant or partner is a qualifying parent or carer"
    documentation = (
        "Whether the claimant or partner has a child or young person placed "
        "with them as a foster child or for adoption (see "
        "is_child_or_young_person_placed_with_family), or is an approved "
        "foster parent who has had no child placed with them for at most 52 "
        "weeks (is_approved_foster_parent_without_placement). The claimant "
        "gets one additional bedroom, and is not a young individual for the "
        "shared accommodation rate. The definition also requires a bedroom "
        "in the dwelling additional to those the occupiers use; the model "
        "does not observe the dwelling's bedrooms and assumes there is one."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/21",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # HB Regs 2006 reg 2(1), "qualifying parent or carer", (a): a child
        # or young person placed with them as mentioned in reg 21(3).
        placed = person("is_child_or_young_person_placed_with_family", period)
        # (b): an approved foster parent with no placement for at most 52
        # weeks.
        between_placements = person("is_claimant_or_partner", period) & person(
            "is_approved_foster_parent_without_placement", period
        )
        return benunit.any(placed | between_placements)

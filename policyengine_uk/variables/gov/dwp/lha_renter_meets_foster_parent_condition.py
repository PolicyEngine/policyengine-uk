from policyengine_uk.model_api import *


class lha_renter_meets_foster_parent_condition(Variable):
    value_type = bool
    entity = BenUnit
    label = "Universal Credit renter meets the foster parent condition"
    documentation = (
        "Whether the renter or a joint renter is a foster parent or an "
        "adopter with whom a child has been placed for adoption. A foster "
        "parent has a child under 18 looked after by a local authority "
        "placed with them (a member of the benefit unit flagged "
        "is_looked_after_by_local_authority), or is an approved foster "
        "parent whose last placement ended, or who was approved, within 12 "
        "months (is_approved_foster_parent_without_placement). The renter "
        "gets one additional bedroom however many children are placed, and "
        "is excepted from the shared accommodation rate."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/29",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        # UC Regs 2013 reg 2, "foster parent": a person with whom a child
        # (under 18) is placed under the care planning regulations; reg 89(3)
        # and Sch 4 para 12(4)(b): an adopter with whom a child is placed for
        # adoption.
        age_limit = parameters(period).gov.dwp.LHA.foster_child_age_limit
        placed_for_adoption = (
            person("is_placed_for_adoption", period)
            & (person("age", period) < age_limit)
            & ~claimant_or_partner
        )
        placed = person("is_lha_foster_child", period) | placed_for_adoption
        # UC Regs 2013 Sch 4 para 12(4)(a)-(b) and (5).
        between_placements = claimant_or_partner & person(
            "is_approved_foster_parent_without_placement", period
        )
        return benunit.any(placed | between_placements)

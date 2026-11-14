from policyengine_uk.model_api import *


class wales_childcare_offer_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "eligibility for the Childcare Offer for Wales"
    documentation = (
        "Whether this family has a qualifying child and every parent meets "
        "the parent conditions of the Childcare Offer for Wales (guidance "
        "para 59: both parents in a couple, or the lone parent)."
    )
    definition_period = YEAR
    defined_for = "would_claim_wales_childcare_offer"
    reference = "https://www.gov.wales/sites/default/files/publications/2026-04/childcare-offer-for-wales-guidance-for-local-authorities-april-2026-english_0.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        has_qualifying_child = benunit.any(
            person("wales_childcare_offer_qualifying_child", period)
        )
        claimant_or_partner = person("is_claimant_or_partner", period)
        parents_meet_conditions = benunit.any(claimant_or_partner) & benunit.all(
            person("wales_childcare_offer_parent_condition", period)
            | ~claimant_or_partner
        )
        return has_qualifying_child & parents_meet_conditions

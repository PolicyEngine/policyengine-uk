from policyengine_uk.model_api import *


class ashford_council_tax_reduction_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Ashford Council Tax Reduction earnings disregard"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.ashford.council_tax_reduction
        has_uc_award = benunit("universal_credit", period) > 0
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        gross_earnings = benunit.sum(
            claimant_or_partner
            * (
                person("employment_income", period)
                + person("self_employment_income", period)
            )
        )
        uc_earned_income = benunit("uc_earned_income", period)
        has_earnings = where(has_uc_award, uc_earned_income > 0, gross_earnings > 0)
        return has_earnings * ctr.earnings_disregard.amount * WEEKS_IN_YEAR

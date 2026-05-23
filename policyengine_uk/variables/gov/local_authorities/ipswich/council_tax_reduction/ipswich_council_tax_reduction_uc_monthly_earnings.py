from policyengine_uk.model_api import *


class ipswich_council_tax_reduction_uc_monthly_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Ipswich Council Tax Reduction Universal Credit notified monthly net earnings"
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.ipswich.gov.uk/sites/ipswich/files/2026-03/Council%20Tax%20Reduction%20scheme%202026_0.pdf"

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        uc_gross_earnings = benunit.sum(
            claimant_or_partner * person("uc_mif_capped_earned_income", period)
        )
        deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period)
            )
        )
        return max_(0, uc_gross_earnings - deductions) / MONTHS_IN_YEAR

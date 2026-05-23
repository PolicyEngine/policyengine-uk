from policyengine_uk.model_api import *


class babergh_council_tax_reduction_uc_monthly_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Babergh Council Tax Reduction Universal Credit notified monthly net earnings"
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.babergh.gov.uk/documents/d/babergh/bdc-ctr-scheme-2026_27-v4-pdf"
    )

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

from policyengine_uk.model_api import *


class slough_council_tax_reduction_weekly_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Slough Council Tax Support weekly net earned income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.slough.gov.uk/downloads/file/5730/council-tax-support-scheme-2026-27"

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_young_person = person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        claimant_or_partner = person("is_adult", period) & ~child_or_young_person
        gross_earned_income = benunit.sum(
            claimant_or_partner
            * (
                person("employment_income", period)
                + person("self_employment_income", period)
            )
        )
        non_uc_deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period) * 0.5
            )
        )
        non_uc_earnings = max_(0, gross_earned_income - non_uc_deductions)
        uc_gross_earnings = benunit.sum(
            claimant_or_partner * person("uc_mif_capped_earned_income", period)
        )
        uc_deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period)
            )
        )
        uc_earnings = max_(0, uc_gross_earnings - uc_deductions)
        has_uc_award = benunit("universal_credit", period) > 0
        annual_earnings = where(has_uc_award, uc_earnings, non_uc_earnings)
        return annual_earnings / WEEKS_IN_YEAR

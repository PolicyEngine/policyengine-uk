from policyengine_uk.model_api import *


class barnet_council_tax_reduction_monthly_earnings(Variable):
    value_type = float
    entity = BenUnit
    label = "Barnet CTS monthly net earnings"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
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
        non_uc_deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period) * 0.5
            )
        )
        non_uc_earnings = max_(0, gross_earnings - non_uc_deductions)
        has_uc = benunit("universal_credit", period) > 0
        uc_deductions = benunit.sum(
            claimant_or_partner
            * (
                person("income_tax", period)
                + person("national_insurance", period)
                + person("pension_contributions", period)
            )
        )
        uc_earnings = max_(
            0,
            add(benunit, period, ["uc_mif_capped_earned_income"]) - uc_deductions,
        )
        annual_earnings = where(has_uc, uc_earnings, non_uc_earnings)
        return annual_earnings / MONTHS_IN_YEAR

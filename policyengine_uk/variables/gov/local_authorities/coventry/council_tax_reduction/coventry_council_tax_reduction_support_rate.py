from policyengine_uk.model_api import *


class coventry_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Coventry Council Tax Reduction support rate"
    definition_period = YEAR
    reference = "https://www.coventry.gov.uk/downloads/file/46761/council-tax-support-scheme-2026-to-2027"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.coventry.council_tax_reduction
        has_uc_award = (
            max_(
                benunit("universal_credit_pre_benefit_cap", period),
                benunit("universal_credit", period),
            )
            > 0
        )
        applicable_amount = where(
            has_uc_award,
            benunit("uc_maximum_amount", period),
            benunit("council_tax_reduction_applicable_amount", period),
        )
        non_uc_applicable_income = benunit(
            "council_tax_reduction_applicable_income", period
        )
        uc_applicable_income = benunit(
            "coventry_council_tax_reduction_uc_applicable_income", period
        )
        applicable_income = where(
            has_uc_award, uc_applicable_income, non_uc_applicable_income
        )
        excess_income = max_(0, applicable_income - applicable_amount)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        excess_income = where(relevant_income_based_benefit, 0, excess_income)
        return ctr.income_band.support_rate.calc(excess_income / WEEKS_IN_YEAR)

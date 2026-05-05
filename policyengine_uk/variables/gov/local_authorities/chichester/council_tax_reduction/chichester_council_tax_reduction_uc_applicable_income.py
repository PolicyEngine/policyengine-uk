from policyengine_uk.model_api import *


class chichester_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Chichester Council Tax Reduction Universal Credit applicable income"
    definition_period = YEAR
    unit = GBP
    reference = "https://chichester.moderngov.co.uk/documents/s30863/09.1%20Appendix%201%20Local%20Council%20Tax%20Reduction%20Scheme%20Rules%202026%20-%202027.pdf"

    def formula(benunit, period, parameters):
        uc_award_before_deductions = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        has_uc_award = uc_award_before_deductions > 0
        counted_uc_award = max_(
            0,
            uc_award_before_deductions
            - benunit("uc_housing_costs_element", period)
            - benunit("uc_disability_elements", period),
        )
        source_uc_income = benunit(
            "chichester_council_tax_reduction_source_uc_income", period
        )
        uc_income_for_banding = where(
            source_uc_income > 0, source_uc_income, counted_uc_award
        )
        return has_uc_award * uc_income_for_banding

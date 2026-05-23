from policyengine_uk.model_api import *


class ashford_council_tax_reduction_childcare_deduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Ashford Council Tax Reduction childcare deduction from earnings"
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )

    def formula(benunit, period, parameters):
        has_uc_award = benunit("universal_credit", period) > 0
        childcare_expenses = benunit.sum(benunit.members("childcare_expenses", period))
        uc_childcare_cap = benunit("uc_maximum_childcare_element_amount", period)
        tax_credits = benunit("tax_credits", period)
        return (
            (tax_credits > 0)
            * ~has_uc_award
            * min_(childcare_expenses, uc_childcare_cap)
        )

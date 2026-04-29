from policyengine_uk.model_api import *


class meets_child_tax_credit_criteria_for_targeted_childcare_entitlement(Variable):
    value_type = bool
    entity = BenUnit
    label = "meets Child Tax Credit criteria for targeted childcare entitlement"
    definition_period = YEAR
    reference = (
        "The Local Authority (Duty to Secure Early Years Provision Free of Charge) "
        "(Amendment) Regulations 2018, regulation 2(a)(i)"
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dfe.targeted_childcare_entitlement
        child_tax_credit = benunit("child_tax_credit", period) > 0
        working_tax_credit = benunit("working_tax_credit", period) > 0
        applicable_income = benunit("tax_credits_applicable_income", period)

        return (
            child_tax_credit
            & ~working_tax_credit
            & (applicable_income <= p.income_limit.tax_credits)
        )

from policyengine_uk.model_api import *


class meets_working_tax_credit_criteria_for_targeted_childcare_entitlement(Variable):
    value_type = bool
    entity = BenUnit
    label = "meets Working Tax Credit criteria for targeted childcare entitlement"
    definition_period = YEAR
    reference = (
        "The Local Authority (Duty to Secure Early Years Provision Free of Charge) "
        "Regulations 2014, regulation 1(2)(b)"
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dfe.targeted_childcare_entitlement
        working_tax_credit = benunit("working_tax_credit", period) > 0
        applicable_income = benunit("tax_credits_applicable_income", period)

        return working_tax_credit & (applicable_income <= p.income_limit.tax_credits)

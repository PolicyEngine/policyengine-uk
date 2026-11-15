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
        # "an annual gross income not exceeding £16,190" (SI 2014/2147 reg
        # 1(2), "eligible child"): the income before TCA 2002 s.7(2) lifts the
        # tax credit income test, not the nil income the test then applies to.
        gross_income = benunit("tax_credits_current_year_income", period)

        return (
            child_tax_credit
            & ~working_tax_credit
            & (gross_income <= p.income_limit.tax_credits)
        )

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
        # "an award which is based on an annual income not exceeding £16,190"
        # (SI 2014/2147 reg 1(2), "eligible child"). The model reads this as
        # the claim's income before TCA 2002 s.7(2) lifts the income test;
        # the nil income a passported award is tested on would let any
        # passported award through, whatever the family's income.
        income = benunit("tax_credits_current_year_income", period)

        return working_tax_credit & (income <= p.income_limit.tax_credits)

from policyengine_uk.model_api import *


class meets_universal_credit_criteria_for_targeted_childcare_entitlement(
    Variable
):
    value_type = bool
    entity = BenUnit
    label = (
        "meets Universal Credit criteria for targeted childcare entitlement"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dfe.targeted_childcare_entitlement

        # Check if receiving Universal Credit
        uc = benunit("universal_credit", period)

        # For Universal Credit recipients, we must use the definition of "earned income"
        # The Local Authority (Duty to Secure Early Years Provision Free of Charge) (Amendment) Regulations 2018 - part 2.c
        # https://www.legislation.gov.uk/uksi/2018/146/made

        # UC-specific earned income as specified by 2(c)(3)(a) of the Regulations
        earned_income = benunit("uc_earned_income", period)

        return (uc > 0) & (earned_income <= p.income_limit.universal_credit)

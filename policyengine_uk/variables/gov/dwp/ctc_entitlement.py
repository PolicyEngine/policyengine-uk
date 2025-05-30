from policyengine_uk.model_api import *


class ctc_entitlement(Variable):
    label = "CTC entitlement"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(benunit, period, parameters):
        return where(
            benunit("tax_credits", period) > 0,
            benunit("child_tax_credit_pre_minimum", period),
            0,
        ) * (benunit("is_CTC_eligible", period))

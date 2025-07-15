from policyengine_uk.model_api import *


class wtc_entitlement(Variable):
    label = "WTC entitlement"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "is_WTC_eligible"

    def formula(benunit, period, parameters):
        return where(
            benunit("tax_credits", period) > 0,
            benunit("working_tax_credit_pre_minimum", period),
            0,
        )

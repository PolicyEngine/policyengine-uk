from policyengine_uk.model_api import *


class pension_credit_entitlement(Variable):
    label = "PC entitlement"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        gc = benunit("guarantee_credit", period)
        sc = benunit("savings_credit", period)
        eligible = benunit("is_pension_credit_eligible", period)
        return eligible * (gc + sc)

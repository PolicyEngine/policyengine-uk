from policyengine_uk.model_api import *


class income_support_entitlement(Variable):
    label = "IS entitlement"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(benunit, period, parameters):
        amount = benunit("income_support_applicable_amount", period)
        income = benunit("income_support_applicable_income", period)
        eligible = benunit("income_support_eligible", period)
        return max_(0, amount - income) * eligible

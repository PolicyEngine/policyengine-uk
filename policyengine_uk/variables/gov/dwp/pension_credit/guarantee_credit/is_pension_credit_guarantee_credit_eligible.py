from policyengine_uk.model_api import *


class is_pension_credit_guarantee_credit_eligible(Variable):
    label = "Guarantee Credit eligible"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool
    unit = GBP

    def formula(benunit, period, parameters):
        income = benunit("pension_credit_income", period)
        minimum_guarantee = benunit("pension_credit_minimum_guarantee", period)
        return income < minimum_guarantee

from policyengine_uk.model_api import *


class jsa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "JSA (income-based)"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        return benunit("jsa_income_reported", period)

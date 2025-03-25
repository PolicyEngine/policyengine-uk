from policyengine_uk.model_api import *


class jsa_income_reported(Variable):
    value_type = float
    entity = Person
    label = "JSA (income-based) (reported amount)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.consumer_price_index"


class jsa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "JSA (income-based)"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        return benunit("jsa_income_reported", period)


class jsa(Variable):
    value_type = float
    entity = BenUnit
    label = "Amount of Jobseeker's Allowance for this family"
    definition_period = YEAR
    unit = GBP
    adds = ["jsa_income", "jsa_contrib"]

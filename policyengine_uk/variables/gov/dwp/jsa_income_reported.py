from policyengine_uk.model_api import *


class jsa_income_reported(Variable):
    value_type = float
    entity = Person
    label = "JSA (income-based) (reported amount)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

from policyengine_uk.model_api import *


class esa_income_reported(Variable):
    value_type = float
    entity = Person
    label = "ESA (income-based) (reported amount)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.consumer_price_index"


class esa_income(Variable):
    value_type = float
    entity = BenUnit
    label = "ESA (income-based)"
    documentation = "Employment and Support Allowance"
    definition_period = YEAR
    unit = GBP

    adds = ["esa_income_reported"]

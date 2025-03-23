from policyengine_uk.model_api import *


class esa_contrib(Variable):
    value_type = float
    entity = Person
    label = "ESA (contribution-based)"
    definition_period = YEAR
    unit = GBP

    adds = ["esa_contrib_reported"]


class esa_contrib_reported(Variable):
    value_type = float
    entity = Person
    label = "Employment and Support Allowance (contribution-based) (reported)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.consumer_price_index"


class esa(Variable):
    label = "ESA"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["esa_contrib", "esa_income"]

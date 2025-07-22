from policyengine_uk.model_api import *


class free_school_milk(Variable):
    label = "free school milk"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

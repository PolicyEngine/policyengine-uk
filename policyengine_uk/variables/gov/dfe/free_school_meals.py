from policyengine_uk.model_api import *


class free_school_meals(Variable):
    label = "free school meals"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

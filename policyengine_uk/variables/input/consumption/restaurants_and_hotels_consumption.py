from policyengine_uk.model_api import *


class restaurants_and_hotels_consumption(Variable):
    label = "restaurants and hotels consumption"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


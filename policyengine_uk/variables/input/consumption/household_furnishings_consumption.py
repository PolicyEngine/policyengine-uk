from policyengine_uk.model_api import *


class household_furnishings_consumption(Variable):
    label = "household furnishings consumption"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

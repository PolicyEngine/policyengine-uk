from policyengine_uk.model_api import *


class petrol_consumption(Variable):
    label = "petrol consumption"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

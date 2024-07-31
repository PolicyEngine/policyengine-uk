from policyengine_uk.model_api import *


class diesel_consumption(Variable):
    label = "diesel consumption"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

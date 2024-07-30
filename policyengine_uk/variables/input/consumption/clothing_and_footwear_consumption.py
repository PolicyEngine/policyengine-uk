from policyengine_uk.model_api import *


class clothing_and_footwear_consumption(Variable):
    label = "clothing and footwear consumption"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

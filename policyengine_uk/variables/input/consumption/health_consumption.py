from policyengine_uk.model_api import *


class health_consumption(Variable):
    label = "health consumption"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

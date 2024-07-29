from policyengine_uk.model_api import *


class other_consumption(Variable):
    label = "other consumption"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


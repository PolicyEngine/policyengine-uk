from policyengine_uk.model_api import *


class transport_consumption(Variable):
    label = "transport consumption"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


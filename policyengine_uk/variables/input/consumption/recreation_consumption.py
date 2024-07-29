from policyengine_uk.model_api import *


class recreation_consumption(Variable):
    label = "recreation consumption"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


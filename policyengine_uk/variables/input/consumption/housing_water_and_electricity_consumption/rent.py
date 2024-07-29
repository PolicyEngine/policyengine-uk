from policyengine_uk.model_api import *


class rent(Variable):
    label = "rent"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


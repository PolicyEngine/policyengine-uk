from policyengine_uk.model_api import *


class other_non_mortgage_interest_consumption(Variable):
    label = "other consumption (excluding mortgage interest)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


from policyengine_uk.model_api import *


class education_consumption(Variable):
    label = "education consumption"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


from policyengine_uk.model_api import *


class original_weight(Variable):
    label = "Original FRS weight"
    entity = Household
    definition_period = YEAR
    value_type = float

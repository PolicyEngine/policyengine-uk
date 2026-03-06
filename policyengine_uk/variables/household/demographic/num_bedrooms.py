from policyengine_uk.model_api import *


class num_bedrooms(Variable):
    value_type = int
    entity = Household
    label = "The number of bedrooms in the house"
    definition_period = YEAR

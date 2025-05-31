from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class num_bedrooms(Variable):
    value_type = int
    entity = Household
    label = "The number of bedrooms in the house"
    definition_period = YEAR

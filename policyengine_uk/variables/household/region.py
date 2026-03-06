from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class region(Variable):
    value_type = Enum
    possible_values = Region
    default_value = Region.LONDON
    entity = Household
    label = "region"
    documentation = "Area of the UK"
    definition_period = YEAR

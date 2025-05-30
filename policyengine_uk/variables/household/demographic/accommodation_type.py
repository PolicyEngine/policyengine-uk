from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class accommodation_type(Variable):
    value_type = Enum
    possible_values = AccommodationType
    default_value = AccommodationType.UNKNOWN
    entity = Household
    label = "Type of accommodation"
    definition_period = YEAR

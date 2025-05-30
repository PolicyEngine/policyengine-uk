from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class AccommodationType(Enum):
    HOUSE_DETACHED = "House - detached"
    HOUSE_SEMI_DETACHED = "House - semi-detached"
    HOUSE_TERRACED = "House - terraced"
    FLAT = "Flat"
    BEDSIT = "Bedsit"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class accommodation_type(Variable):
    value_type = Enum
    possible_values = AccommodationType
    default_value = AccommodationType.UNKNOWN
    entity = Household
    label = "Type of accommodation"
    definition_period = YEAR

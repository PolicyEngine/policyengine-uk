from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class AccommodationType(Enum):
    HOUSE_DETACHED = "Detached house"
    HOUSE_SEMI_DETACHED = "Semi-detached house"
    HOUSE_TERRACED = "Terraced house"
    FLAT = "Purpose-built flat or maisonette"
    CONVERTED_HOUSE = "Converted house or building"
    MOBILE = "Caravan/Mobile home or houseboat"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class accommodation_type(Variable):
    value_type = Enum
    possible_values = AccommodationType
    default_value = AccommodationType.UNKNOWN
    entity = Household
    label = "Type of accommodation"
    definition_period = YEAR

from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class TenureType(Enum):
    RENT_FROM_COUNCIL = "Rent from council"
    RENT_FROM_HA = "Rent from housing association"
    RENT_PRIVATELY = "Rent privately"
    OWNER_OCCUPIED = "Owner occupied"


class tenure_type(Variable):
    value_type = Enum
    possible_values = TenureType
    default_value = TenureType.RENT_PRIVATELY
    entity = Household
    label = "Tenure type of the household"
    definition_period = YEAR

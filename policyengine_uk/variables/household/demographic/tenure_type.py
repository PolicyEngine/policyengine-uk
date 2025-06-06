from policyengine_uk.model_api import *


class TenureType(Enum):
    RENT_FROM_COUNCIL = "Rented from Council"
    RENT_FROM_HA = "Rented from a Housing Association"
    RENT_PRIVATELY = "Rented privately"
    OWNED_OUTRIGHT = "Owned outright"
    OWNED_WITH_MORTGAGE = "Owned with a mortgage"


class tenure_type(Variable):
    value_type = Enum
    possible_values = TenureType
    default_value = TenureType.RENT_PRIVATELY
    entity = Household
    label = "Tenure type of the household"
    definition_period = YEAR

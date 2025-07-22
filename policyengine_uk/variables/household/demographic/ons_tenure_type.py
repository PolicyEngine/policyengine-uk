from policyengine_uk.model_api import *


class ONSTenureType(Enum):
    OWNER_OCCUPIED = "Owner occupied"
    RENT_PRIVATELY = "Rent privately"
    RENT_FROM_COUNCIL = "Rent from council"
    RENT_FROM_HA = "Rent from housing association"


class ons_tenure_type(Variable):
    label = "ONS tenure type"
    documentation = "Tenure type matching ONS_produced statistical breakdowns."
    entity = Household
    definition_period = YEAR
    value_type = Enum
    possible_values = ONSTenureType
    default_value = ONSTenureType.OWNER_OCCUPIED

    def formula(household, period, parameters):
        tenure = household("tenure_type", period)
        tenure_types = tenure.possible_values
        return select(
            [
                tenure == tenure_types.RENT_FROM_HA,
                tenure == tenure_types.RENT_FROM_COUNCIL,
                tenure == tenure_types.RENT_PRIVATELY,
            ],
            [
                ONSTenureType.RENT_FROM_HA,
                ONSTenureType.RENT_FROM_COUNCIL,
                ONSTenureType.RENT_PRIVATELY,
            ],
            default=ONSTenureType.OWNER_OCCUPIED,
        )

from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region

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
        return select(
            [
                tenure == TenureType.RENT_FROM_HA,
                tenure == TenureType.RENT_FROM_COUNCIL,
                tenure == TenureType.RENT_PRIVATELY,
                tenure == TenureType.OWNED_OUTRIGHT,
                tenure == TenureType.OWNED_WITH_MORTGAGE,
            ],
            [
                ONSTenureType.RENT_FROM_HA,
                ONSTenureType.RENT_FROM_COUNCIL,
                ONSTenureType.RENT_PRIVATELY,
                ONSTenureType.OWNER_OCCUPIED,
                ONSTenureType.OWNER_OCCUPIED,
            ],
        )

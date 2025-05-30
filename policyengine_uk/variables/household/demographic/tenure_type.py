from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region

class tenure_type(Variable):
    value_type = Enum
    possible_values = TenureType
    default_value = TenureType.RENT_PRIVATELY
    entity = Household
    label = "Tenure type of the household"
    definition_period = YEAR

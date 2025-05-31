from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class is_shared_accommodation(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is shared accommodation"
    definition_period = YEAR

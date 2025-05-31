from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class households(Variable):
    value_type = float
    entity = Household
    label = "Variable holding households"
    definition_period = YEAR
    default_value = 1

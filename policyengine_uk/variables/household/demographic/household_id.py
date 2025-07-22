from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class household_id(Variable):
    value_type = int
    entity = Household
    label = "ID for the household"
    definition_period = YEAR

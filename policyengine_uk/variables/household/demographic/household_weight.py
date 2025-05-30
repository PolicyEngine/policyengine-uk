from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class household_weight(Variable):
    value_type = float
    entity = Household
    label = "Weight factor for the household"
    definition_period = YEAR
    uprating = "gov.ons.population"
    default_value = 1

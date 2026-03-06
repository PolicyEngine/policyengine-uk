from policyengine_uk.model_api import *


class household_weight(Variable):
    value_type = float
    entity = Household
    label = "Weight factor for the household"
    definition_period = YEAR
    uprating = "gov.economic_assumptions.indices.ons.population"
    default_value = 1

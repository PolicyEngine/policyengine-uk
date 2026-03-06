from policyengine_uk.model_api import *


class household_id(Variable):
    value_type = int
    entity = Household
    label = "ID for the household"
    definition_period = YEAR

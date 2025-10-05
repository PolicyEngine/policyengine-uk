from policyengine_uk.model_api import *


class household_owns_tv_seed(Variable):
    value_type = float
    entity = Household
    label = "Random seed for TV ownership"
    definition_period = YEAR

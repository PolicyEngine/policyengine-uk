from policyengine_uk.model_api import *


class first_home_purchase_seed(Variable):
    value_type = float
    entity = Household
    label = "Random seed for first home purchase determination"
    definition_period = YEAR

from policyengine_uk.model_api import *


class child_benefit_take_up_seed(Variable):
    value_type = float
    entity = BenUnit
    label = "Random seed for child benefit take-up"
    definition_period = YEAR

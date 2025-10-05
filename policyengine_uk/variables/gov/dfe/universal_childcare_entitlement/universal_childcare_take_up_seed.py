from policyengine_uk.model_api import *


class universal_childcare_take_up_seed(Variable):
    value_type = float
    entity = BenUnit
    label = "Random seed for universal childcare take-up"
    definition_period = YEAR

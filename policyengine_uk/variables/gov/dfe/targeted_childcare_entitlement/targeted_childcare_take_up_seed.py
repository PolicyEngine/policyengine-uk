from policyengine_uk.model_api import *


class targeted_childcare_take_up_seed(Variable):
    value_type = float
    entity = BenUnit
    label = "Random seed for targeted childcare take-up"
    definition_period = YEAR

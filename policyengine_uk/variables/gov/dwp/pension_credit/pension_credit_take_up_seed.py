from policyengine_uk.model_api import *


class pension_credit_take_up_seed(Variable):
    value_type = float
    entity = BenUnit
    label = "Random seed for pension credit take-up"
    definition_period = YEAR

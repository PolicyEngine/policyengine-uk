from policyengine_uk.model_api import *


class tax_free_childcare_take_up_seed(Variable):
    value_type = float
    entity = BenUnit
    label = "Random seed for Tax-Free Childcare take-up"
    definition_period = YEAR

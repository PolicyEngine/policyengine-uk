from policyengine_uk.model_api import *


class is_higher_earner_seed(Variable):
    value_type = float
    entity = Person
    label = "Random seed for tie-breaking in higher earner determination"
    definition_period = YEAR

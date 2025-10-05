from policyengine_uk.model_api import *


class attends_private_school_seed(Variable):
    value_type = float
    entity = Person
    label = "Random seed for private school attendance"
    definition_period = YEAR

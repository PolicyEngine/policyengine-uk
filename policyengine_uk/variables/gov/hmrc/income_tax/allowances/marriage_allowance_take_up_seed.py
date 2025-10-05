from policyengine_uk.model_api import *


class marriage_allowance_take_up_seed(Variable):
    value_type = float
    entity = Person
    label = "Random seed for marriage allowance take-up"
    definition_period = YEAR

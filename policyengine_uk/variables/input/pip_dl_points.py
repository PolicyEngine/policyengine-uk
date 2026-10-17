from policyengine_uk.model_api import *


class pip_dl_points(Variable):
    label = "PIP daily living points"
    documentation = "Total descriptor points scored across the ten Schedule 1 Part 2 daily living activities. Used to derive `pip_dl_category` when the category is not provided as input."
    entity = Person
    definition_period = YEAR
    value_type = int
    default_value = 0

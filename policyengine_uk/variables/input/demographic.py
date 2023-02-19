from policyengine_uk.model_api import *

label = "Demographic"
description = "Demographic variables."


class age(Variable):
    value_type = float
    entity = Person
    label = "age"
    unit = "year"
    documentation = "Age in years"
    definition_period = YEAR
    quantity_type = STOCK
    default_value = 40

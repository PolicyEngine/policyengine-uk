from policyengine_uk.model_api import *

label = "Demographic"
description = "Demographic variables."


class age(Variable):
    value_type = float
    entity = Person
    label = "age"
    unit = "year"
    value_type = float
    documentation = "Age in years."
    definition_period = YEAR
    quantity_type = STOCK
    default_value = 40


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


class gender(Variable):
    label = "gender"
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = Gender
    default_value = Gender.MALE

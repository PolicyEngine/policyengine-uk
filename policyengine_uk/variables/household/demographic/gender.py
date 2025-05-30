from policyengine_uk.model_api import *
import pandas as pd

class gender(Variable):
    value_type = Enum
    possible_values = Gender
    default_value = Gender.MALE
    entity = Person
    label = "Gender of the person"
    definition_period = YEAR

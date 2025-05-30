from policyengine_uk.model_api import *
import pandas as pd

class highest_education(Variable):
    value_type = Enum
    possible_values = EducationType
    default_value = EducationType.UPPER_SECONDARY
    entity = Person
    label = "Highest status education completed"
    definition_period = YEAR

from policyengine_uk.model_api import *
import datetime
import numpy as np


class employment_status(Variable):
    value_type = Enum
    entity = Person
    possible_values = EmploymentStatus
    default_value = EmploymentStatus.UNEMPLOYED
    label = "Employment status of the person"
    definition_period = YEAR

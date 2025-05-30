from policyengine_uk.model_api import *
import datetime
import numpy as np


class EmploymentStatus(Enum):
    CHILD = "Child"
    UNEMPLOYED = "Unemployed"
    EMPLOYED = "Employed"
    SELF_EMPLOYED = "Self-employed"
    RETIRED = "Retired"
    STUDENT = "Student"
    CARER = "Carer"
    LONG_TERM_SICK = "Long-term sick"
    SHORT_TERM_SICK = "Short-term sick"


class employment_status(Variable):
    value_type = Enum
    entity = Person
    possible_values = EmploymentStatus
    default_value = EmploymentStatus.UNEMPLOYED
    label = "Employment status of the person"
    definition_period = YEAR

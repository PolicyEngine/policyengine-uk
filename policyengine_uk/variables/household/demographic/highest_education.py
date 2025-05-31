from policyengine_uk.model_api import *
import pandas as pd


class EducationType(Enum):
    NOT_IN_EDUCATION = "Not in education"
    PRE_PRIMARY = "Pre-primary"
    NOT_COMPLETED_PRIMARY = "Not completed primary"
    PRIMARY = "Primary"
    LOWER_SECONDARY = "Lower Secondary"
    UPPER_SECONDARY = "Upper Secondary"
    POST_SECONDARY = "Post Secondary"
    TERTIARY = "Tertiary"


class highest_education(Variable):
    value_type = Enum
    possible_values = EducationType
    default_value = EducationType.UPPER_SECONDARY
    entity = Person
    label = "Highest status education completed"
    definition_period = YEAR

from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)
import pandas as pd


class current_education(Variable):
    value_type = Enum
    possible_values = EducationType
    default_value = EducationType.NOT_IN_EDUCATION
    entity = Person
    label = "Current education"
    definition_period = YEAR

    def formula(person, period, parameters):
        if (
            person.get_holder("current_education").get_array(period.last_year)
            is not None
        ):
            return person("current_education", period.last_year)
        age = person("age", period)
        return np.select(
            [
                age < 4,
                (age >= 4) & (age < 7),
                (age >= 7) & (age < 11),
                (age >= 11) & (age < 14),
                (age >= 14) & (age < 16),
                (age >= 16) & (age < 18),
                (age >= 18) & (age < 20),
                age >= 20,
            ],
            [
                EducationType.PRE_PRIMARY,
                EducationType.NOT_COMPLETED_PRIMARY,
                EducationType.PRIMARY,
                EducationType.LOWER_SECONDARY,
                EducationType.UPPER_SECONDARY,
                EducationType.POST_SECONDARY,
                EducationType.TERTIARY,
                EducationType.NOT_IN_EDUCATION,
            ],
        )

from policyengine_uk.model_api import *
import datetime
import numpy as np

class minimum_wage_category(Variable):
    value_type = Enum
    possible_values = MinimumWageCategory
    default_value = MinimumWageCategory.OVER_24
    entity = Person
    label = "Minimum wage category"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        return select(
            [
                person("is_apprentice", period),
                age < 18,
                (age >= 18) & (age <= 20),
                (age >= 21) & (age <= 22),
                (age >= 23) & (age <= 24),
            ],
            [
                MinimumWageCategory.APPRENTICE,
                MinimumWageCategory.UNDER_18,
                MinimumWageCategory.BETWEEN_18_20,
                MinimumWageCategory.BETWEEN_21_22,
                MinimumWageCategory.BETWEEN_23_24,
            ],
            default=MinimumWageCategory.OVER_24,
        )

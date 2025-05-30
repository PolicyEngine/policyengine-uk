from policyengine_uk.model_api import *
import pandas as pd


class adult_index(Variable):
    value_type = int
    entity = Person
    label = "Index of adult in household"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (
            person.get_rank(
                person.household,
                -person("age", period),
                condition=person("is_adult", period),
            )
            + 1
        )

from policyengine_uk.model_api import *
import pandas as pd


class age_18_64(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is age 18 to 64"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        return (age >= 18) & (age <= 64)

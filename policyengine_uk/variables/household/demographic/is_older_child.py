from policyengine_uk.model_api import *
import pandas as pd


class is_older_child(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is over 14 but under 18"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        return (age >= 14) & (age < 18)

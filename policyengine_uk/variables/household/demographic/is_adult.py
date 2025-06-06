from policyengine_uk.model_api import *
import pandas as pd


class is_adult(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is an adult"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) >= 18

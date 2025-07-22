from policyengine_uk.model_api import *
import pandas as pd


class age_under_18(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is under age 18"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) < 18

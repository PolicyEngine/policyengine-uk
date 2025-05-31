from policyengine_uk.model_api import *
import pandas as pd


class age_over_64(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is over age 64"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) > 64

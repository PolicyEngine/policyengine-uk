from policyengine_uk.model_api import *
import pandas as pd


class over_16(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is over 16"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) >= 16

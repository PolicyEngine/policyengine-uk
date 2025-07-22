from policyengine_uk.model_api import *
import pandas as pd


class is_young_child(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is under 14"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) < 14

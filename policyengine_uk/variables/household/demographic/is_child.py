from policyengine_uk.model_api import *
import pandas as pd


class is_child(Variable):
    value_type = bool
    entity = Person
    label = "Is a child"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) < 18

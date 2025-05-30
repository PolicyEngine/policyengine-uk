from policyengine_uk.model_api import *
import pandas as pd


class is_female(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is female"
    definition_period = YEAR

    def formula(person, period, parameters):
        gender = person("gender", period)
        return gender == gender.possible_values.FEMALE

from policyengine_uk.model_api import *
import pandas as pd


class is_male(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is male"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("gender", period) == Gender.MALE

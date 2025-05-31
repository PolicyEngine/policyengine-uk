from policyengine_uk.model_api import *
import pandas as pd


class is_WA_adult(Variable):
    value_type = bool
    entity = Person
    label = "Whether is a working-age adult"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("is_adult", period) & ~person("is_SP_age", period)

from policyengine_uk.model_api import *
import pandas as pd


class person_weight(Variable):
    value_type = float
    entity = Person
    label = "Weight"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person.household("household_weight", period)

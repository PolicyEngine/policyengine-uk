from policyengine_uk.model_api import *
import pandas as pd


class is_benunit_head(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is the head-of-family"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person.get_rank(person.benunit, person("age", period)) == 0

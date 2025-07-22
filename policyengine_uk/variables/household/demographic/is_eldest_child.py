from policyengine_uk.model_api import *
import pandas as pd


class is_eldest_child(Variable):
    label = "Is the eldest child"
    documentation = (
        "Whether this person is the eldest child in the benefit unit"
    )
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        index = person("child_index", period)
        index = where(index < 0, 100, index)
        lowest_index = person.benunit.min(index)
        return index == lowest_index

from policyengine_uk.model_api import *
import pandas as pd


class is_eldest_child(Variable):
    label = "Eldest benefit-unit member under 18 (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use the programme's own child index instead."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        index = person("child_index", period)
        index = where(index < 0, 100, index)
        lowest_index = person.benunit.min(index)
        return index == lowest_index

from policyengine_uk.model_api import *
import pandas as pd


class is_young_child(Variable):
    value_type = bool
    entity = Person
    label = "Aged under 14 (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use is_hbai_child_under_14 instead."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) < 14

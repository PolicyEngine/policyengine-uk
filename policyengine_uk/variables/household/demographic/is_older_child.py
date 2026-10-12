from policyengine_uk.model_api import *
import pandas as pd


class is_older_child(Variable):
    value_type = bool
    entity = Person
    label = "Aged 14 to 17 (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use is_hbai_child_aged_14_or_over instead."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        return (age >= 14) & (age < 18)

from policyengine_uk.model_api import *
import pandas as pd


class is_child(Variable):
    value_type = bool
    entity = Person
    label = "Aged under 18 (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use age_under_18 for the age band, is_hbai_dependent_child for HBAI statistics, or the programme's own child definition (for example is_child_or_qualifying_young_person_for_universal_credit) instead."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) < 18

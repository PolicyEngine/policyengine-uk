from policyengine_uk.model_api import *
import pandas as pd


class is_WA_adult(Variable):
    value_type = bool
    entity = Person
    label = "Aged 18 to below State Pension age (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use is_hbai_working_age_adult for HBAI statistics, or the programme's own age conditions instead."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("is_adult", period) & ~person("is_SP_age", period)

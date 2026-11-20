from policyengine_uk.model_api import *
import pandas as pd


class is_adult(Variable):
    value_type = bool
    entity = Person
    label = "Aged 18 or over (deprecated)"
    documentation = (
        "Deprecated: an age cut-off with no legal basis, kept only for "
        "downstream compatibility with its original formula. Nothing in "
        "policyengine-uk uses it. Use the negation of age_under_18 for the age band, is_hbai_adult for HBAI statistics, or is_claimant_or_partner for the claimant and partner of a benefit unit instead."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) >= 18

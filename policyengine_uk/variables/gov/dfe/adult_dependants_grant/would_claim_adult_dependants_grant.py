from policyengine_uk.model_api import *


class would_claim_adult_dependants_grant(Variable):
    value_type = bool
    entity = Person
    label = "Would claim Adult Dependants' Grant"
    documentation = (
        "Whether this person would claim Adult Dependants' Grant if eligible."
    )
    definition_period = YEAR
    default_value = True

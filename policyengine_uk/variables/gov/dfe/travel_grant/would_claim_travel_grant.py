from policyengine_uk.model_api import *


class would_claim_travel_grant(Variable):
    value_type = bool
    entity = Person
    label = "Would claim Travel Grant"
    documentation = "Whether this person would claim Travel Grant if eligible."
    definition_period = YEAR
    default_value = True

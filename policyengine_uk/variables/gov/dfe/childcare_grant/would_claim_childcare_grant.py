from policyengine_uk.model_api import *


class would_claim_childcare_grant(Variable):
    value_type = bool
    entity = Person
    label = "Would claim Childcare Grant"
    documentation = "Whether this person would claim Childcare Grant if eligible."
    definition_period = YEAR
    default_value = True

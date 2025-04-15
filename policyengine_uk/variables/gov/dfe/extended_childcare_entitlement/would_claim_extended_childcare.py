from policyengine_uk.model_api import *


class would_claim_extended_childcare(Variable):
    value_type = bool
    entity = BenUnit
    label = "would claim extended childcare entitlement"
    documentation = "Whether this family would claim extended childcare entitlement if eligible"
    definition_period = YEAR
    default_value = True

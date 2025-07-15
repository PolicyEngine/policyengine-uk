from policyengine_uk.model_api import *


class would_claim_universal_childcare(Variable):
    value_type = bool
    entity = ben_unit
    label = "would claim universal childcare entitlement"
    documentation = "Whether this ben_unit would claim universal childcare entitlement if eligible"
    definition_period = YEAR
    default_value = True

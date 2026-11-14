from policyengine_uk.model_api import *


class would_claim_universal_childcare(Variable):
    value_type = bool
    entity = BenUnit
    label = "would claim universal childcare entitlement"
    documentation = (
        "Whether this BenUnit would claim universal childcare entitlement on "
        "its own if eligible. Working parent participation still allocates "
        "the child's first funded hours to universal provision."
    )
    definition_period = YEAR
    default_value = True

from policyengine_uk.model_api import *


class would_claim_targeted_childcare(Variable):
    value_type = bool
    entity = BenUnit
    label = "would claim targeted childcare entitlement"
    documentation = (
        "Whether this family would claim targeted childcare entitlement on "
        "its own if eligible. Working parent participation still allocates "
        "the child's first funded hours to targeted provision."
    )
    definition_period = YEAR
    default_value = True

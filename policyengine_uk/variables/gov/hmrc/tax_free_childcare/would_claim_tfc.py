from policyengine_uk.model_api import *


class would_claim_tfc(Variable):
    value_type = bool
    entity = BenUnit
    label = "would claim Tax-Free Childcare"
    documentation = (
        "Whether this family would claim Tax-Free Childcare if eligible"
    )
    definition_period = YEAR
    default_value = True

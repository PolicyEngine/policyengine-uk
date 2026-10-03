from policyengine_uk.model_api import *


class would_claim_uc_at_legacy_closure(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Universal Credit when its legacy benefits close"
    documentation = (
        "Whether this family would claim Universal Credit once a legacy "
        "means-tested benefit it receives closes (legacy_benefits_closed). "
        "Datasets draw it at DWP's Move to Universal Credit claim rates by "
        "legacy benefit combination. It does not affect years before the "
        "closure, when would_claim_uc alone decides the Universal Credit "
        "claim. Defaults to True, like would_claim_uc."
    )
    definition_period = YEAR
    default_value = True

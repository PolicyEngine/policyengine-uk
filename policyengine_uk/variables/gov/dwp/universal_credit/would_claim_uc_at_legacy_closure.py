from policyengine_uk.model_api import *


class would_claim_uc_at_legacy_closure(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Universal Credit when its legacy benefits close"
    documentation = (
        "Whether this family would claim Universal Credit once a legacy "
        "means-tested benefit it receives closes (legacy_benefits_closed), "
        "or once the abolition of income-related ESA reaches the claimant's "
        "or partner's award (esa_income_abolition_reached, from 2026-27). "
        "Datasets draw it at DWP's Move to Universal Credit claim rates by "
        "legacy benefit combination. It does not affect years before the "
        "closure or the abolition, when would_claim_uc alone decides the "
        "Universal Credit claim. Defaults to True, like would_claim_uc, so a "
        "family whose data carries no draw claims."
    )
    definition_period = YEAR
    default_value = True

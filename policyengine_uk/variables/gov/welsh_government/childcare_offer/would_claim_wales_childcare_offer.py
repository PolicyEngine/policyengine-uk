from policyengine_uk.model_api import *


class would_claim_wales_childcare_offer(Variable):
    value_type = bool
    entity = BenUnit
    label = "would claim the Childcare Offer for Wales"
    documentation = (
        "Whether this family would claim the Childcare Offer for Wales if eligible"
    )
    definition_period = YEAR
    default_value = True

from policyengine_uk.model_api import *


class would_claim_care_to_learn(Variable):
    value_type = bool
    entity = BenUnit
    label = "would claim Care to Learn"
    documentation = (
        "Whether this BenUnit would claim Care to Learn if eligible"
    )
    definition_period = YEAR
    default_value = True

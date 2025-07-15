from policyengine_uk.model_api import *


class would_claim_care_to_learn(Variable):
    value_type = bool
    entity = ben_unit
    label = "would claim Care to Learn"
    documentation = (
        "Whether this ben_unit would claim Care to Learn if eligible"
    )
    definition_period = YEAR
    default_value = True

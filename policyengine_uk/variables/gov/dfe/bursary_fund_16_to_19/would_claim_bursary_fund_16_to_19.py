from policyengine_uk.model_api import *


class would_claim_bursary_fund_16_to_19(Variable):
    value_type = bool
    entity = Person
    label = "Would claim 16 to 19 Bursary Fund support"
    documentation = (
        "Whether this person would claim 16 to 19 Bursary Fund support if eligible."
    )
    definition_period = YEAR
    default_value = True

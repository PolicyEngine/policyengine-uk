from policyengine_uk.model_api import *


class income_support(Variable):
    value_type = float
    entity = BenUnit
    label = "Income Support"
    definition_period = YEAR
    unit = GBP
    defined_for = "would_claim_IS"
    adds = ["income_support_entitlement"]

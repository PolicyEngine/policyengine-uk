from policyengine_uk.model_api import *


class child_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = "Child Tax Credit"
    definition_period = YEAR
    unit = GBP
    defined_for = "would_claim_CTC"
    adds = ["ctc_entitlement"]

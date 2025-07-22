from policyengine_uk.model_api import *


class working_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit"
    definition_period = YEAR
    unit = GBP
    defined_for = "would_claim_WTC"
    adds = ["wtc_entitlement"]

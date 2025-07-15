from policyengine_uk.model_api import *


class universal_credit_pre_benefit_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit before benefit cap"
    documentation = "Total entitlement to Universal Credit"
    definition_period = YEAR
    unit = GBP
    category = BENEFIT
    defined_for = "would_claim_uc"

    adds = ["uc_maximum_amount"]
    subtracts = ["uc_income_reduction"]

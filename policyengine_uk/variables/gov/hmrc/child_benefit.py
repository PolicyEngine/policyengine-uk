from policyengine_uk.model_api import *


class child_benefit(Variable):
    label = "Child Benefit"
    documentation = "Total Child Benefit for the benefit unit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    category = BENEFIT
    defined_for = "would_claim_child_benefit"
    adds = ["child_benefit_entitlement"]

from policyengine_uk.model_api import *


class extended_childcare_entitlement(Variable):
    value_type = float
    entity = BenUnit
    label = "annual extended childcare entitlement expenses"
    documentation = (
        "The annual value of the working parent hours for the family's "
        "children, over and above their universal and targeted hours. See "
        "extended_childcare_entitlement_per_child."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "extended_childcare_entitlement_eligible"
    adds = ["extended_childcare_entitlement_per_child"]

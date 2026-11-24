from policyengine_uk.model_api import *


class would_claim_uc_housing_costs_element(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim the Universal Credit housing costs element"
    documentation = (
        "Whether this family's Universal Credit award would include the "
        "housing costs element if entitled. False stands for an award that "
        "carries no housing costs element for a reason the model doesn't "
        "simulate: housing costs not claimed or not yet verified, or a "
        "liability DWP doesn't treat as eligible. A family with it false gets "
        "no element under any reform, so a dataset should set it false only "
        "where the model would otherwise pay an element. Defaults to true."
    )
    definition_period = YEAR
    default_value = True

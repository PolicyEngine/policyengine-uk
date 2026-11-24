from policyengine_uk.model_api import *


class would_claim_uc_housing_costs_element(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim the Universal Credit housing costs element"
    documentation = (
        "Whether this family's Universal Credit award would include the "
        "housing costs element if entitled. A dataset sets it false where a "
        "renting family's award statement carries no housing costs element; "
        "for the policy calculator it defaults to True."
    )
    definition_period = YEAR
    default_value = True

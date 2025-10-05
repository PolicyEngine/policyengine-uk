from policyengine_uk.model_api import *


class would_claim_targeted_childcare(Variable):
    value_type = bool
    entity = BenUnit
    label = "would claim targeted childcare entitlement"
    documentation = (
        "Whether this family would claim targeted childcare entitlement if eligible. "
        "Generated stochastically in the dataset using take-up rates."
    )
    definition_period = YEAR

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to True
    default_value = True

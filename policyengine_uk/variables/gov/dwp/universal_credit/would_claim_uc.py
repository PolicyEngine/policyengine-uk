from policyengine_uk.model_api import *


class would_claim_uc(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Universal Credit"
    documentation = (
        "Whether this family would claim the Universal Credit if eligible. "
        "Generated stochastically in the dataset using take-up rates."
    )
    definition_period = YEAR

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to True
    default_value = True

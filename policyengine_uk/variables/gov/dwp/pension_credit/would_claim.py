from policyengine_uk.model_api import *


class would_claim_pc(Variable):
    label = "Would claim Pension Credit"
    documentation = (
        "Whether this benefit unit would claim Pension Credit if eligible. "
        "Generated stochastically in the dataset using take-up rates."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to True
    default_value = True

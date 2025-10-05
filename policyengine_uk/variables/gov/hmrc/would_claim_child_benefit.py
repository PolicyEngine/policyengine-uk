from policyengine_uk.model_api import *


class would_claim_child_benefit(Variable):
    label = "Would claim Child Benefit"
    documentation = (
        "Whether this benefit unit would claim Child Benefit if eligible. "
        "Generated stochastically in the dataset using take-up rates."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to True
    default_value = True

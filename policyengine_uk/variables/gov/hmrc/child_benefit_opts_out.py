from policyengine_uk.model_api import *


class child_benefit_opts_out(Variable):
    label = "opts out of Child Benefit"
    documentation = (
        "Whether this family would opt out of receiving Child Benefit payments. "
        "Generated stochastically in the dataset using opt-out rates."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to False
    default_value = False

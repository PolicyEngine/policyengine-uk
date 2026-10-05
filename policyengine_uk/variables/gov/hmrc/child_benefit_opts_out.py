from policyengine_uk.model_api import *


class child_benefit_opts_out(Variable):
    label = "opts out of Child Benefit"
    documentation = (
        "Whether this family would opt out of Child Benefit payments because "
        "of the High Income Child Benefit Charge. Generated in the dataset "
        "using opt-out rates. Payments resume when the simulated policy no "
        "longer charges the family; entitlement and the separate decision "
        "whether to claim are unchanged."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to False
    default_value = False

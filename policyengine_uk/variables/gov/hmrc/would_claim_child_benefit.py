from policyengine_uk.model_api import *


class would_claim_child_benefit(Variable):
    label = "Would claim Child Benefit"
    documentation = (
        "Whether this benefit unit would claim Child Benefit if eligible. "
        "Microcosm exports this as claims excluding payment opt-outs; a true "
        "child_benefit_opts_out flag therefore also identifies a registered claim. "
        "Set both flags false for a genuine nonclaimant. Household calculators "
        "default to claiming unless supplied otherwise."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to True
    default_value = True

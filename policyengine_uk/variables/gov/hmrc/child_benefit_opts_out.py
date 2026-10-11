from policyengine_uk.model_api import *


class child_benefit_opts_out(Variable):
    label = "opts out of Child Benefit"
    documentation = (
        "Whether a family would opt out of Child Benefit payments because of the "
        "High Income Child Benefit Charge. This is independent of "
        "would_claim_child_benefit and never identifies a claim by itself. "
        "For claimants, payments resume when the simulated charge share falls below "
        "the assumed "
        "opt_out_charge_share threshold (one by default), or the charge is zero "
        "or neutralised. Entitlement and nonclaimant status are unchanged."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to False
    default_value = False

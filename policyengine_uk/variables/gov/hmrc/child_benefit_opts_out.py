from policyengine_uk.model_api import *


class child_benefit_opts_out(Variable):
    label = "opts out of Child Benefit"
    documentation = (
        "Whether a family would opt out of Child Benefit payments because of the "
        "High Income Child Benefit Charge. This is independent of "
        "would_claim_child_benefit and never identifies a claim by itself. "
        "For claimants, payments resume when the continuous charge share (the "
        "unrounded share of the phase-out band crossed) falls below the assumed "
        "opt_out_charge_share threshold (one by default), or is zero, or the "
        "charge is neutralised. The statutory charge itself is rounded "
        "(ITEPA 2003 s. 681C(3)) and can be nil where the share is small but "
        "positive. Entitlement and nonclaimant status are unchanged."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to False
    default_value = False

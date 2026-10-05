from policyengine_uk.model_api import *


class child_benefit_opts_out(Variable):
    label = "opts out of Child Benefit"
    documentation = (
        "Whether a registered claimant opts out of Child Benefit payments because "
        "of the High Income Child Benefit Charge. A true value also identifies a "
        "claim when would_claim_child_benefit is false, as in Microcosm exports. "
        "Payments resume when the simulated charge share falls below the assumed "
        "opt_out_charge_share threshold (one by default), or the charge is zero "
        "or neutralised. Entitlement is unchanged. Legacy data with independently "
        "drawn flags must clear opt-outs for genuine nonclaimants before loading."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to False
    default_value = False

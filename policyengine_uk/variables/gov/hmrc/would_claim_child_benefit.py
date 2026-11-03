from policyengine_uk.model_api import *


class would_claim_child_benefit(Variable):
    label = "Would claim Child Benefit"
    documentation = (
        "Whether this benefit unit would claim Child Benefit if eligible, "
        "including registered claimants who opt out of payment. This claim flag "
        "is independent of child_benefit_opts_out; false always means no payment. "
        "Datasets must export claims rather than claims excluding opt-outs. "
        "Household calculators default to claiming unless supplied otherwise."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to True
    default_value = True

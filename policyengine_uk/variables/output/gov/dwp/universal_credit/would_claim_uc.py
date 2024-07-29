from policyengine_uk.model_api import *


class would_claim_uc(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Universal Credit"
    documentation = (
        "Whether this family would claim the Universal Credit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        current_uc_claimant = (
            add(benunit, period, ["universal_credit_reported"]) > 0
        )
        brought_into_claim = benunit(
            "is_brought_into_uc_claimant_status", period
        )
        is_in_microsimulation = hasattr(benunit.simulation, "dataset")
        if is_in_microsimulation:
            return current_uc_claimant | brought_into_claim
        return True

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
        takes_up = (
            random(benunit)
            < parameters(period).gov.dwp.universal_credit.takeup_rate
        )
        is_in_microsimulation = benunit.simulation.dataset is not None
        if is_in_microsimulation:
            return takes_up
        return True

from policyengine_uk.model_api import *


class would_claim_universal_childcare(Variable):
    value_type = bool
    entity = BenUnit
    label = "would claim universal childcare entitlement"
    documentation = "Whether this BenUnit would claim universal childcare entitlement if eligible"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        takeup_rate = parameters(period).gov.dfe.universal_childcare_entitlement.takeup_rate
        is_in_microsimulation = benunit.simulation.dataset is not None
        if is_in_microsimulation:
            return benunit("universal_childcare_take_up_seed", period) < takeup_rate
        return True

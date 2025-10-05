from policyengine_uk.model_api import *


class would_claim_targeted_childcare(Variable):
    value_type = bool
    entity = BenUnit
    label = "would claim targeted childcare entitlement"
    documentation = "Whether this family would claim targeted childcare entitlement if eligible"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        takeup_rate = parameters(period).gov.dfe.targeted_childcare_entitlement.takeup_rate
        is_in_microsimulation = benunit.simulation.dataset is not None
        if is_in_microsimulation:
            return benunit("targeted_childcare_take_up_seed", period) < takeup_rate
        return True

from policyengine_uk.model_api import *


class would_claim_tfc(Variable):
    value_type = bool
    entity = BenUnit
    label = "would claim Tax-Free Childcare"
    documentation = (
        "Whether this family would claim Tax-Free Childcare if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        takeup_rate = parameters(period).gov.hmrc.tax_free_childcare.takeup_rate
        is_in_microsimulation = benunit.simulation.dataset is not None
        if is_in_microsimulation:
            return benunit("tax_free_childcare_take_up_seed", period) < takeup_rate
        return True

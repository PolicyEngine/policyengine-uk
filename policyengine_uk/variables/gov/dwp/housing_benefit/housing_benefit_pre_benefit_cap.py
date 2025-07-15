from policyengine_uk.model_api import *


class housing_benefit_pre_benefit_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit pre-benefit cap"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        eligible = benunit("housing_benefit_eligible", period)
        would_claim = benunit("would_claim_housing_benefit", period)
        return where(
            eligible & would_claim,
            benunit("housing_benefit_entitlement", period),
            0,
        )

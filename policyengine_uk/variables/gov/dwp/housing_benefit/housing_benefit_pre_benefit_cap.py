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
        # A working-age award abolished part-way through the year is paid
        # for the part before the abolition date.
        payable_share = benunit("housing_benefit_payable_share", period)
        return where(
            eligible & would_claim,
            benunit("housing_benefit_entitlement", period) * payable_share,
            0,
        )

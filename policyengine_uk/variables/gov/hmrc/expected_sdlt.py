from policyengine_uk.model_api import *


class expected_sdlt(Variable):
    label = "Stamp Duty (expected)"
    documentation = "Expected value of Stamp Duty Land Tax"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        if parameters(period).gov.hmrc.stamp_duty.abolish:
            return 0
        return (
            household("stamp_duty_land_tax", period)
            + parameters(period).gov.hmrc.stamp_duty.property_sale_rate
        ) + household("corporate_sdlt", period)

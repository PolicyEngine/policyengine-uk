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
            household.state("property_sale_rate", period)
            * household("stamp_duty_land_tax", period)
        ) + household("corporate_sdlt", period)

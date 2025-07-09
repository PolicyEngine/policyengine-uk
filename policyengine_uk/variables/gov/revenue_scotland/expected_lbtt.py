from policyengine_uk.model_api import *


class expected_lbtt(Variable):
    label = "Land and Buildings Transaction Tax (expected)"
    documentation = "Expected value of LBTT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        property_sale_rate = parameters(
            period
        ).gov.hmrc.stamp_duty.property_sale_rate
        lbtt = household("land_and_buildings_transaction_tax", period)
        return property_sale_rate * lbtt

from policyengine_uk.model_api import *


class property_sale_rate(Variable):
    label = "Residential property sale rate"
    documentation = "The percentage of residential property value owned by households sold in the year"
    entity = State
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(household, period, parameters):
        return parameters(period).gov.hmrc.stamp_duty.property_sale_rate

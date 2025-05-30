from policyengine_uk.model_api import *


class sdlt_on_non_residential_property_transactions(Variable):
    label = "Stamp Duty on non-residential property"
    documentation = "Tax charge from purchase of non-residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/14/section/55"

    def formula(household, period, parameters):
        stamp_duty = parameters(period).gov.hmrc.stamp_duty
        price = household("non_residential_property_purchased", period)
        return stamp_duty.non_residential.purchase.calc(price)

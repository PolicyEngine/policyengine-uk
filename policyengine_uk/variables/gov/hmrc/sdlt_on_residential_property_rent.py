from policyengine_uk.model_api import *


class sdlt_on_residential_property_rent(Variable):
    label = "Stamp Duty on residential property"
    documentation = "Tax charge from rental of residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/14/schedule/5"

    def formula(household, period, parameters):
        stamp_duty = parameters(period).gov.hmrc.stamp_duty
        cumulative_rent = household("cumulative_residential_rent", period)
        rent = household("rent", period)
        return stamp_duty.residential.rent.calc(
            cumulative_rent + rent
        ) - stamp_duty.residential.rent.calc(cumulative_rent)

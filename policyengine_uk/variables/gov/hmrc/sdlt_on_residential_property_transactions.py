from policyengine_uk.model_api import *


class sdlt_on_residential_property_transactions(Variable):
    label = "Stamp Duty on residential property"
    documentation = "Tax charge from purchase of residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/14/section/55"

    def formula(household, period, parameters):
        stamp_duty = parameters(period).gov.hmrc.stamp_duty
        # Tax on main-home purchases
        price_limit = stamp_duty.residential.purchase.main.first.max
        price = household("main_residential_property_purchased", period)
        residential_purchase_qualifies_as_first_buy = household(
            "main_residential_property_purchased_is_first_home", period
        ) & (price < price_limit)
        main_residential_purchase_tax = where(
            residential_purchase_qualifies_as_first_buy,
            stamp_duty.residential.purchase.main.first.rate.calc(price),
            stamp_duty.residential.purchase.main.subsequent.calc(price),
        )
        # Tax on second-home purchases
        second_home_price = household(
            "additional_residential_property_purchased", period
        )
        price = where(
            second_home_price < stamp_duty.residential.purchase.additional.min,
            0,
            second_home_price,
        )
        additional_residential_purchase_tax = (
            stamp_duty.residential.purchase.additional.rate.calc(price)
        )
        return (
            main_residential_purchase_tax + additional_residential_purchase_tax
        )

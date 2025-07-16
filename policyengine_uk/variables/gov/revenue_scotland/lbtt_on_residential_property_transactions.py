from policyengine_uk.model_api import *


class lbtt_on_residential_property_transactions(Variable):
    label = "LBTT on residential property"
    documentation = "LBTT charge on purchase of residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        p = parameters(period).gov.revenue_scotland.lbtt
        # Tax on main-home purchases
        price = household("main_residential_property_purchased", period)
        residential_purchase_qualifies_as_first_buy = household(
            "main_residential_property_purchased_is_first_home", period
        )
        main_residential_purchase_tax = where(
            residential_purchase_qualifies_as_first_buy,
            p.residential.first_time_buyer_rate.calc(price),
            p.residential.rate.calc(price),
        )
        # Tax on second-home purchases
        second_home_price = household(
            "additional_residential_property_purchased", period
        )
        lbtt2 = p.residential.rate.calc(second_home_price)
        surcharge = (
            p.residential.additional_residence_surcharge * second_home_price
        )
        additional_residential_purchase_tax = lbtt2 + surcharge
        return (
            main_residential_purchase_tax + additional_residential_purchase_tax
        )

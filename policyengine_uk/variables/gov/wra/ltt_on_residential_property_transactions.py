from policyengine_uk.model_api import *


class ltt_on_residential_property_transactions(Variable):
    label = "LTT on residential property"
    documentation = (
        "Land Transaction Tax charge on residential property transactions"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        ltt = parameters(period).gov.wra.land_transaction_tax
        main_home_price = household(
            "main_residential_property_purchased", period
        )
        primary_residential_purchase_tax = ltt.residential.primary.calc(
            main_home_price
        )
        second_home_price = household(
            "additional_residential_property_purchased", period
        )
        additional_residential_purchase_tax = ltt.residential.higher_rate.calc(
            second_home_price
        )
        return (
            primary_residential_purchase_tax
            + additional_residential_purchase_tax
        )

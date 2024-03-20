from policyengine_uk.model_api import *


class lbtt_on_residential_property_transactions(Variable):
    label = "LBTT on residential property"
    documentation = "LBTT charge on purchase of residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        lbtt = parameters(period).gov.revenue_scotland.lbtt
        # Tax on main-home purchases
        price = household("main_residential_property_purchased", period)
        residential_purchase_qualifies_as_first_buy = household(
            "main_residential_property_purchased_is_first_home", period
        )
        main_residential_purchase_tax = where(
            residential_purchase_qualifies_as_first_buy,
            lbtt.residential.first_time_buyer_rate.calc(price),
            lbtt.residential.rate.calc(price),
        )
        # Tax on second-home purchases
        second_home_price = household(
            "additional_residential_property_purchased", period
        )
        lbtt2 = lbtt.residential.rate.calc(second_home_price)
        surcharge = (
            lbtt.residential.additional_residence_surcharge * second_home_price
        )
        additional_residential_purchase_tax = lbtt2 + surcharge
        return (
            main_residential_purchase_tax + additional_residential_purchase_tax
        )


class lbtt_on_residential_property_rent(Variable):
    label = "LBTT on residential property rent"
    documentation = "LBTT charge on rental of residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        lbtt = parameters(period).gov.revenue_scotland.lbtt
        cumulative_rent = household("cumulative_residential_rent", period)
        rent = household("rent", period)
        lbtt_cumulative_rent = lbtt.rent.calc(cumulative_rent)
        lbtt_total_rent = lbtt.rent.calc(cumulative_rent + rent)
        return lbtt_total_rent - lbtt_cumulative_rent


class lbtt_on_non_residential_property_transactions(Variable):
    label = "LBTT on non-residential property transactions"
    documentation = "LBTT charge from purchase of non-residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        lbtt = parameters(period).gov.revenue_scotland.lbtt
        price = household("non_residential_property_purchased", period)
        return lbtt.non_residential.calc(price)


class lbtt_on_non_residential_property_rent(Variable):
    label = "LBTT on non-residential property"
    documentation = (
        "LBTT charge from purchase or rental of non-residential property"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        lbtt = parameters(period).gov.revenue_scotland.lbtt
        cumulative_rent = household("cumulative_non_residential_rent", period)
        rent = household("non_residential_rent", period)
        lbtt_cumulative_rent = lbtt.rent.calc(cumulative_rent)
        lbtt_total_rent = lbtt.rent.calc(cumulative_rent + rent)
        return lbtt_total_rent - lbtt_cumulative_rent


class lbtt_liable(Variable):
    label = "Liable for Land and Buildings Transaction Tax"
    documentation = "Whether the household is liable for Land and Buildings Transaction Tax"
    entity = Household
    definition_period = YEAR
    value_type = bool
    unit = GBP

    def formula(household, period):
        country = household("country", period)
        countries = country.possible_values
        return country == countries.SCOTLAND


class lbtt_on_transactions(Variable):
    label = "LBTT on property transactions"
    documentation = "Land and Buildings Transaction Tax on property transfers"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = [
        "lbtt_on_residential_property_transactions",
        "lbtt_on_non_residential_property_transactions",
    ]


class lbtt_on_rent(Variable):
    label = "LBTT on property rental"
    documentation = (
        "Land and Buildings Transaction Tax on property rental agreements"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = [
        "lbtt_on_residential_property_rent",
        "lbtt_on_non_residential_property_rent",
    ]


class land_and_buildings_transaction_tax(Variable):
    label = "Land and Buildings Transaction Tax"
    documentation = "Total tax liability for Scotland's LBTT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        LBTTS = [
            "lbtt_on_transactions",
            "lbtt_on_rent",
        ]
        lbtt_if_liable = add(household, period, LBTTS)
        return household("lbtt_liable", period) * lbtt_if_liable


class expected_lbtt(Variable):
    label = "Land and Buildings Transaction Tax (expected)"
    documentation = "Expected value of LBTT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        property_sale_rate = household.state("property_sale_rate", period)
        lbtt = household("land_and_buildings_transaction_tax", period)
        return property_sale_rate * lbtt


class baseline_expected_lbtt(Variable):
    label = "LBTT (expected, baseline)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP


class change_in_expected_lbtt(Variable):
    label = "average per-year LBTT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    formula = change_over_baseline(expected_lbtt)

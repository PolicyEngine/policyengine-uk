from policyengine_uk.model_api import *


class ltt_liable(Variable):
    label = "Liable for Land Transaction Tax"
    documentation = (
        "Whether the household is liable to pay the Wales Land Transaction Tax"
    )
    entity = Household
    definition_period = YEAR
    value_type = bool

    def formula(household, period):
        country = household("country", period)
        return country == country.possible_values.WALES


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


class ltt_on_residential_property_rent(Variable):
    label = "LTT on residential property rent"
    documentation = (
        "Land Transaction Tax charge on residential property rental agreements"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        ltt = parameters(period).gov.wra.land_transaction_tax
        cumulative_rent = household("cumulative_residential_rent", period)
        rent = household("rent", period)
        ltt_on_cumulative_rent = ltt.rent.calc(cumulative_rent)
        ltt_on_total_rent = ltt.rent.calc(cumulative_rent + rent)
        return ltt_on_total_rent - ltt_on_cumulative_rent


class ltt_on_non_residential_property_transactions(Variable):
    label = "LTT on non-residential property transactions"
    documentation = (
        "Land Transaction Tax charge on non-residential property transactions"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        ltt = parameters(period).gov.wra.land_transaction_tax
        price = household("non_residential_property_purchased", period)
        non_residential_purchase_tax = ltt.non_residential.calc(price)
        return household("ltt_liable", period) * non_residential_purchase_tax


class ltt_on_non_residential_property_rent(Variable):
    label = "LTT on non-residential property rent"
    documentation = "Land Transaction Tax charge on non-residential property rental agreements"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        ltt = parameters(period).gov.wra.land_transaction_tax
        cumulative_rent = household("cumulative_non_residential_rent", period)
        rent = household("non_residential_rent", period)
        ltt_on_cumulative_rent = ltt.rent.calc(cumulative_rent)
        ltt_on_total_rent = ltt.rent.calc(cumulative_rent + rent)
        return ltt_on_total_rent - ltt_on_cumulative_rent


class ltt_on_transactions(Variable):
    label = "LTT on property transactions"
    documentation = "Land Transaction Tax on property transfers"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        LTT_TRANSACTION_VARIABLES = [
            "ltt_on_residential_property_transactions",
            "ltt_on_non_residential_property_transactions",
        ]
        return add(household, period, LTT_TRANSACTION_VARIABLES)


class ltt_on_rent(Variable):
    label = "LTT on property rental"
    documentation = "Land Transaction Tax on property rental agreements"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        LTT_RENT_VARIABLES = [
            "ltt_on_residential_property_rent",
            "ltt_on_non_residential_property_rent",
        ]
        return add(household, period, LTT_RENT_VARIABLES)


class land_transaction_tax(Variable):
    label = "Land Transaction Tax"
    documentation = "Total tax liability for Land Transaction Tax"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        ltt_if_liable = add(
            household, period, ["ltt_on_transactions", "ltt_on_rent"]
        )
        return household("ltt_liable", period) * ltt_if_liable


class expected_ltt(Variable):
    label = "Land Transaction Tax (expected)"
    documentation = "Expected value of Land Transaction Tax"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        property_sale_rate = household.state("property_sale_rate", period)
        land_transaction_tax = household("land_transaction_tax", period)
        return property_sale_rate * land_transaction_tax


class baseline_expected_ltt(Variable):
    label = "Land Transaction Tax (baseline, expected)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP


class change_in_expected_ltt(Variable):
    label = "average per-year LTT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    formula = change_over_baseline(expected_ltt)

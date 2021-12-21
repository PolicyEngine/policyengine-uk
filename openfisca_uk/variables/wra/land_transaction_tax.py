from openfisca_uk.model_api import *


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
    unit = "currency-GBP"

    def formula(household, period, parameters):
        ltt = parameters(period).wra.land_transaction_tax
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
    unit = "currency-GBP"

    def formula(household, period, parameters):
        ltt = parameters(period).wra.land_transaction_tax
        cumulative_rent = household("cumulative_residential_rent", period)
        rent = household("rent", period)
        return ltt.rent.calc(cumulative_rent + rent) - ltt.rent.calc(
            cumulative_rent
        )


class ltt_on_non_residential_property_transactions(Variable):
    label = "LTT on non-residential property transactions"
    documentation = (
        "Land Transaction Tax charge on non-residential property transactions"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        ltt = parameters(period).wra.land_transaction_tax
        price = household("non_residential_property_purchased", period)
        non_residential_purchase_tax = ltt.non_residential.calc(price)
        return household("ltt_liable", period) * non_residential_purchase_tax


class ltt_on_non_residential_property_rent(Variable):
    label = "LTT on non-residential property rent"
    documentation = "Land Transaction Tax charge on non-residential property rental agreements"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        ltt = parameters(period).wra.land_transaction_tax
        cumulative_rent = household("cumulative_non_residential_rent", period)
        rent = household("non_residential_rent", period)
        return ltt.rent.calc(cumulative_rent + rent) - ltt.rent.calc(
            cumulative_rent
        )


class ltt_on_transactions(Variable):
    label = "LTT on property transactions"
    documentation = "Land Transaction Tax on property transfers"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period):
        return household(
            "ltt_on_residential_property_transactions", period
        ) + household("ltt_on_non_residential_property_transactions", period)


class ltt_on_rent(Variable):
    label = "LTT on property rental"
    documentation = "Land Transaction Tax on property rental agreements"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period):
        return household(
            "ltt_on_residential_property_rent", period
        ) + household("ltt_on_non_residential_property_rent", period)


class land_transaction_tax(Variable):
    label = "Land Transaction Tax"
    documentation = "Total tax liability for Land Transaction Tax"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period):
        return household("ltt_liable", period) * (
            household("ltt_on_transactions", period)
            + household("ltt_on_rent", period)
        )


class expected_ltt(Variable):
    label = "Land Transaction Tax (expected)"
    documentation = "Expected value of Land Transaction Tax"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period):
        return household.state("property_sale_rate", period) * household(
            "land_transaction_tax", period
        )

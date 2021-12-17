from openfisca_uk.model_api import *

class ltt_liable(Variable):
    label = "Liable for Land Transaction Tax"
    documentation = "Whether the household is liable to pay the Land Transaction Tax"
    entity = Household
    definition_period = YEAR
    value_type = bool

    def formula(household, period):
        country = household("country", period)
        return country == country.possible_values.WALES

class ltt_on_residential_property(Variable):
    label = "LTT on residential property"
    documentation = "Land Transaction Tax charge on residential property value"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        ltt = parameters(period).wra.land_transaction_tax
        main_home_price = household("main_residential_property_purchased", period)
        primary_residential_purchase_tax = ltt.residential.primary.calc(main_home_price)
        second_home_price = household(
            "additional_residential_property_purchased", period
        )
        additional_residential_purchase_tax = ltt.residential.higher_rate.calc(second_home_price)
        cumulative_rent = household("cumulative_residential_rent", period)
        rent = household("rent", period)
        rent_tax = ltt.rent.calc(cumulative_rent + rent) - ltt.rent.calc(cumulative_rent)
        return household("ltt_liable", period) * (
            primary_residential_purchase_tax
            + additional_residential_purchase_tax
            + rent_tax
        )

class ltt_on_non_residential_property(Variable):
    label = "LTT on non-residential property"
    documentation = "Land Transaction Tax charge on non-residential property value"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        ltt = parameters(period).wra.land_transaction_tax
        price = household("non_residential_property_purchased", period)
        non_residential_purchase_tax = ltt.non_residential.calc(price)
        return household("ltt_liable", period) * non_residential_purchase_tax

class land_transaction_tax(Variable):
    label = "Land Transaction Tax"
    documentation = "Total tax liability for Land Transaction Tax"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period):
        return (
            household("ltt_on_residential_property", period)
            + household("ltt_on_non_residential_property", period)
        )

class expected_land_transaction_tax(Variable):
    label = "Land Transaction Tax (expected)"
    documentation = "Expected value of Land Transaction Tax"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period):
        return (
            household.state("property_sale_rate", period)
            * household("land_transaction_tax", period)
        )

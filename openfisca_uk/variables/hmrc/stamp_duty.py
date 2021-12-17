from openfisca_uk.model_api import *


class stamp_duty_on_residential_property(Variable):
    label = "Stamp Duty on residential property"
    documentation = (
        "Tax charge from purchase or rental of residential property"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        stamp_duty = parameters(period).hmrc.stamp_duty
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
        # Tax on residential rents
        cumulative_rent = household("cumulative_residential_rent", period)
        rent = household("rent", period)
        residential_rent_tax = stamp_duty.residential.rent.calc(
            cumulative_rent + rent
        ) - stamp_duty.residential.rent.calc(cumulative_rent)
        return household("stamp_duty_liable", period) * (
            main_residential_purchase_tax
            + additional_residential_purchase_tax
            + residential_rent_tax
        )


class stamp_duty_on_non_residential_property(Variable):
    label = "Stamp Duty on non-residential property"
    documentation = (
        "Tax charge from purchase or rental of non-residential property"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        stamp_duty = parameters(period).hmrc.stamp_duty
        # Tax on non-residential purchases
        price = household("non_residential_property_purchased", period)
        non_residential_purchase_tax = (
            stamp_duty.non_residential.purchase.calc(price)
        )
        # Tax on non-residential rents
        cumulative_rent = household("cumulative_non_residential_rent", period)
        rent = household("non_residential_rent", period)
        non_residential_rent_tax = stamp_duty.non_residential.rent.calc(
            cumulative_rent + rent
        ) - stamp_duty.non_residential.rent.calc(cumulative_rent)
        return household("stamp_duty_liable", period) * (
            non_residential_purchase_tax + non_residential_rent_tax
        )


class stamp_duty_liable(Variable):
    label = "Liable for Stamp Duty"
    documentation = "Whether the household is liable for Stamp Duty Land Tax"
    entity = Household
    definition_period = YEAR
    value_type = bool
    unit = "currency-GBP"

    def formula(household, period):
        country = household("country", period)
        countries = country.possible_values
        return np.isin(
            country.decode_to_str(),
            [countries.ENGLAND.name, countries.NORTHERN_IRELAND.name],
        )


class corporate_stamp_duty_revenue(Variable):
    label = "Stamp Duty (corporations)"
    documentation = "Stamp Duty paid by corporations"
    entity = State
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(state, period, parameters):
        sd = parameters(period).hmrc.stamp_duty.statistics
        in_force = not parameters(period).hmrc.stamp_duty.abolition
        return in_force * (
            sd.residential.corporate.revenue
            + sd.non_residential.corporate.revenue
        )


class corporate_stamp_duty_revenue_change(Variable):
    label = "Change in corporate Stamp Duty liabilities"
    documentation = (
        "Tota increase in tax revenues from corporations for Stamp Duty"
    )
    entity = State
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(state, period, parameters):
        sd = parameters(period).hmrc.stamp_duty.statistics
        baseline_sd = (
            sd.residential.corporate.revenue
            + sd.non_residential.corporate.revenue
        )
        return state("corporate_stamp_duty_revenue", period) - baseline_sd


class stamp_duty(Variable):
    label = "Stamp Duty Land Tax"
    documentation = "Total tax liability for Stamp Duty Land Tax"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period):
        return household(
            "stamp_duty_on_residential_property", period
        ) + household("stamp_duty_on_non_residential_property", period)


class expected_stamp_duty(Variable):
    label = "Stamp Duty (expected)"
    documentation = "Expected value of Stamp Duty taxes"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        in_force = not parameters(period).hmrc.stamp_duty.abolition
        return (
            in_force
            * household("property_sale_rate", period)
            * household("stamp_duty", period)
        )

from policyengine_uk.model_api import *


class property_sale_rate(Variable):
    label = "Residential property sale rate"
    documentation = "The percentage of residential property value owned by households sold in the year"
    entity = State
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(household, period, parameters):
        stamp_duty = parameters(period).gov.hmrc.stamp_duty.statistics
        nbs = parameters(period).household.wealth.national_balance_sheet
        total_sale_value = (
            stamp_duty.residential.household.transaction_values
            + stamp_duty.non_residential.household.transaction_values
        )
        total_value = (
            nbs.household.dwellings
            + nbs.household.other_structures
            + nbs.household.land
        )
        return total_sale_value / total_value


class main_residential_property_purchased(Variable):
    label = "Residential property bought (main)"
    documentation = "The price paid for the purchase of a residential property in the year, for use as a main residence. Only include the value of a single purchase."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        property_purchased = household("property_purchased", period)
        main_residence_value = household("main_residence_value", period)
        return main_residence_value * property_purchased


class additional_residential_property_purchased(Variable):
    label = "Residential property bought (additional)"
    documentation = "The price paid for the purchase of a residential property in the year, for use as a second home or another non-main-residence purpose. Only include the value of a single purchase."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        property_purchased = household("property_purchased", period)
        other_residential_property_value = household(
            "other_residential_property_value", period
        )
        return other_residential_property_value * property_purchased


class main_residential_property_purchased_is_first_home(Variable):
    label = "Residential property bought is first home"
    documentation = "Whether the residential property bought this year as a main residence was as a first-time buyer."
    entity = Household
    definition_period = YEAR
    value_type = bool
    unit = GBP

    def formula(household, period, parameters):
        residential_sd = parameters(
            period
        ).gov.hmrc.stamp_duty.statistics.residential.household
        age = household.sum(
            household.members("is_household_head", period)
            * household.members("age", period)
        )
        percentage_claiming_ftbr = (
            residential_sd.first_time_buyers_relief.calc(age)
            / residential_sd.transactions_by_age.calc(age)
        )
        return random(household) < percentage_claiming_ftbr


class non_residential_property_purchased(Variable):
    label = "Non-residential property bought"
    documentation = "The price paid for the purchase of a non-residential property in the year. Only include the value of a single purchase."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "property_purchased"
    adds = ["non_residential_property_value"]


class mortgage(Variable):
    value_type = float
    entity = Household
    label = "total mortgage payments"
    documentation: str = "Total amount spent on mortgage payments"
    definition_period = YEAR
    unit = GBP
    adds = [
        "mortgage_interest_repayment",
        "mortgage_capital_repayment",
    ]

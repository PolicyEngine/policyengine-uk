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


class sdlt_on_non_residential_property_transactions(Variable):
    label = "Stamp Duty on non-residential property"
    documentation = "Tax charge from purchase of non-residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/14/section/55"

    def formula(household, period, parameters):
        stamp_duty = parameters(period).gov.hmrc.stamp_duty
        price = household("non_residential_property_purchased", period)
        return stamp_duty.non_residential.purchase.calc(price)


class sdlt_on_non_residential_property_rent(Variable):
    label = "Stamp Duty on non-residential property"
    documentation = "Tax charge from rental of non-residential property"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/14/schedule/5"

    def formula(household, period, parameters):
        stamp_duty = parameters(period).gov.hmrc.stamp_duty
        cumulative_rent = household("cumulative_non_residential_rent", period)
        rent = household("non_residential_rent", period)
        return stamp_duty.non_residential.rent.calc(
            cumulative_rent + rent
        ) - stamp_duty.non_residential.rent.calc(cumulative_rent)


class sdlt_on_transactions(Variable):
    label = "SDLT on property transactions"
    documentation = "Stamp Duty Land Tax on property transfers"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/14/section/55"

    adds = [
        "sdlt_on_residential_property_transactions",
        "sdlt_on_non_residential_property_transactions",
    ]


class sdlt_on_rent(Variable):
    label = "SDLT on property rental"
    documentation = "Stamp Duty Land Tax on property rental agreements"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/14/section/55"

    adds = [
        "sdlt_on_residential_property_rent",
        "sdlt_on_non_residential_property_rent",
    ]


class sdlt_liable(Variable):
    label = "Liable for Stamp Duty"
    documentation = "Whether the household is liable for Stamp Duty Land Tax"
    entity = Household
    definition_period = YEAR
    value_type = bool
    unit = GBP

    def formula(household, period):
        country = household("country", period)
        countries = country.possible_values
        return np.isin(
            country.decode_to_str(),
            [countries.ENGLAND.name, countries.NORTHERN_IRELAND.name],
        )


class baseline_corporate_sdlt(Variable):
    label = "Stamp Duty (corporations, baseline)"
    documentation = "Stamp Duty paid by corporations, incident on this household in the baseline"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        sd = parameters(period).gov.hmrc.stamp_duty.statistics
        return household("shareholding", period) * (
            sd.residential.corporate.revenue
            + sd.non_residential.corporate.revenue
        )


class corporate_sdlt(Variable):
    label = "Stamp Duty (corporations)"
    documentation = (
        "Stamp Duty paid by corporations, incident on this household"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    formula = baseline_corporate_sdlt.formula


class corporate_sdlt_change_incidence(Variable):
    label = "Change in corporate Stamp Duty (expected)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    formula = change_over_baseline(corporate_sdlt)


class stamp_duty_land_tax(Variable):
    label = "Stamp Duty Land Tax"
    documentation = "Total tax liability for Stamp Duty Land Tax"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/14/part/4"
    defined_for = "sdlt_liable"
    adds = [
        "sdlt_on_transactions",
        "sdlt_on_rent",
    ]


class expected_sdlt(Variable):
    label = "Stamp Duty (expected)"
    documentation = "Expected value of Stamp Duty Land Tax"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period):
        return (
            household.state("property_sale_rate", period)
            * household("stamp_duty_land_tax", period)
        ) + household("corporate_sdlt", period)


class baseline_expected_sdlt(Variable):
    label = "Stamp Duty (expected, baseline)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP


class change_in_expected_sdlt(Variable):
    label = "average per-year Stamp Duty"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    formula = change_over_baseline(expected_sdlt)

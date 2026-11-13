from policyengine_uk.model_api import *


class sdlt_on_residential_property_transactions(Variable):
    label = "Stamp Duty on residential property"
    documentation = (
        "Tax charge from purchase of residential property. HMRC charges a "
        "purchase of an additional dwelling at the higher rates when "
        "gov.hmrc.stamp_duty.residential.purchase.additional.higher_rates_apply "
        "holds true, and at the main rates when it holds false. Ordinary "
        "purchases use whole-price bands before 4 December 2014 and "
        "marginal bands from that date."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/14/section/55"

    def formula(household, period, parameters):
        residential = parameters(period).gov.hmrc.stamp_duty.residential
        if not residential.purchase_in_effect:
            return household.empty_array()

        scale = residential.purchase.main.subsequent

        def main_rates_tax(price):
            if not residential.purchase_charged_on_whole_price:
                return scale.calc(price)
            # The upper limit belongs to the lower band: s. 55 used
            # "not more than", so a price must strictly exceed a threshold.
            thresholds = np.array(scale.thresholds, dtype=float)
            rates = np.array(scale.rates, dtype=float)
            exceeds = np.asarray(price, dtype=float)[:, None] > thresholds[None, :]
            band = exceeds.sum(axis=1) - 1
            whole_rate = where(band >= 0, rates[max_(band, 0)], 0)
            return whole_rate * price

        # Tax on main-home purchases
        price_limit = residential.purchase.main.first.max
        price = household("main_residential_property_purchased", period)
        main_residential_purchase_tax = main_rates_tax(price)
        # The relief's rate schedule is unavailable before its introduction.
        if price_limit > 0:
            residential_purchase_qualifies_as_first_buy = household(
                "main_residential_property_purchased_is_first_home", period
            ) & (price <= price_limit)
            main_residential_purchase_tax = where(
                residential_purchase_qualifies_as_first_buy,
                residential.purchase.main.first.rate.calc(price),
                main_residential_purchase_tax,
            )
        # Tax on second-home purchases: the higher rates for additional
        # dwellings once they apply, and the main rates before then.
        additional = residential.purchase.additional
        second_home_price = household(
            "additional_residential_property_purchased", period
        )
        if additional.higher_rates_apply:
            chargeable = where(second_home_price < additional.min, 0, second_home_price)
            additional_residential_purchase_tax = additional.rate.calc(chargeable)
        else:
            additional_residential_purchase_tax = main_rates_tax(second_home_price)
        return main_residential_purchase_tax + additional_residential_purchase_tax

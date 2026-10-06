from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


class tobacco_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    unit = GBP
    label = "Tobacco duty"
    reference = "https://www.legislation.gov.uk/ukpga/1979/7/schedule/1"

    def formula_2024(household, period, parameters):
        cigarettes = max_(household("cigarettes_per_week", period), 0) * WEEKS_IN_YEAR
        pack_price = max_(household("cigarette_price_per_pack", period), 0)
        pack_size = parameters(period).household.consumption.tobacco.cigarettes_per_pack
        products = {
            "hand_rolling": "hand_rolling_tobacco_grams_per_week",
            "cigars": "cigars_grams_per_week",
            "other": "other_tobacco_grams_per_week",
            "heated": "heated_tobacco_grams_per_week",
        }
        # Unit conversion: grams to kilograms.
        kilograms = {
            product: max_(household(variable, period), 0) * WEEKS_IN_YEAR / 1_000
            for product, variable in products.items()
        }
        total = 0
        for rates, share in fiscal_year_segments(
            parameters.gov.hmrc.tobacco_duty.rates, period.start.year
        ):
            cigarette_rate = max_(
                rates.cigarette_specific
                + rates.cigarette_ad_valorem * pack_price / pack_size,
                rates.cigarette_minimum,
            )
            duty = cigarettes * cigarette_rate
            for product, quantity in kilograms.items():
                duty += quantity * getattr(rates, product)
            total += duty * share
        return total

from policyengine_uk.model_api import *


class monthly_epg_consumption_level(Variable):
    label = "Monthly EPG subsidy level"
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = "currency-GBP"
    reference = (
        "https://www.gov.uk/government/publications/energy-bills-support/energy-price-guarantee-up-until-30-june-2023",
        "https://www.gov.uk/government/publications/energy-price-guarantee-regional-rates/energy-price-guarantee-prepayment-meters-regional-rates-july-to-september-2023",
        "https://www.gov.uk/government/publications/energy-price-guarantee-regional-rates/energy-price-guarantee-prepayment-meters-regional-rates-and-standing-charges-october-to-december-2023",
        "https://www.ofgem.gov.uk/news/new-energy-price-cap-level-april-june-2024-starts-today",
    )

    def formula(household, period, parameters):
        energy_consumption = household("monthly_domestic_energy_consumption", period)
        ofgem = parameters.gov.ofgem
        in_effect = ofgem.energy_price_guarantee_in_effect(period)
        if not in_effect:
            return energy_consumption
        price_cap = ofgem.energy_price_cap(period)
        price_guarantee = ofgem.energy_price_guarantee(period)
        general_consumption_level = energy_consumption * price_guarantee / price_cap

        country = household("country", period)
        countries = country.possible_values
        in_great_britain = (
            (country == countries.ENGLAND)
            | (country == countries.SCOTLAND)
            | (country == countries.WALES)
        )
        uses_prepayment_meter = household("uses_energy_prepayment_meter", period)
        annual_prepayment_discount = ofgem.energy_price_guarantee_prepayment_discount(
            period
        )
        prepayment_consumption_level = max_(
            0,
            min_(energy_consumption, general_consumption_level)
            - annual_prepayment_discount / MONTHS_IN_YEAR,
        )
        receives_prepayment_discount = (
            in_great_britain & uses_prepayment_meter & (annual_prepayment_discount > 0)
        )
        return where(
            receives_prepayment_discount,
            prepayment_consumption_level,
            general_consumption_level,
        )

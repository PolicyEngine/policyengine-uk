from policyengine_uk.model_api import *


class monthly_epg_consumption_level(Variable):
    label = "Monthly EPG subsidy level"
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = "currency-GBP"
    reference = [
        "https://www.gov.uk/government/publications/energy-bills-support/energy-price-guarantee-up-until-30-june-2023",
        "https://www.ofgem.gov.uk/news/new-energy-price-cap-level-april-june-2024-starts-today",
    ]

    def formula(household, period, parameters):
        energy_consumption = household("monthly_domestic_energy_consumption", period)
        ofgem = parameters.gov.ofgem
        price_cap = ofgem.energy_price_cap(period)
        price_guarantee = ofgem.energy_price_guarantee(period)
        guaranteed_consumption = energy_consumption * price_guarantee / price_cap
        return where(
            price_guarantee > 0,
            guaranteed_consumption,
            energy_consumption,
        )

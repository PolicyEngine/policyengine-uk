from policyengine_uk.model_api import *


class monthly_epg_consumption_level(Variable):
    label = "Monthly EPG subsidy level"
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        energy_consumption = household(
            "monthly_domestic_energy_consumption", period
        )
        ofgem = parameters.gov.ofgem
        price_cap = ofgem.energy_price_cap(period)
        price_guarantee = ofgem.energy_price_guarantee(period)
        return energy_consumption * price_guarantee / price_cap

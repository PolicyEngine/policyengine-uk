from policyengine_uk.model_api import *


class monthly_epg_subsidy(Variable):
    label = "Monthly EPG subsidy"
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        energy_consumption = household(
            "monthly_domestic_energy_consumption", period
        )
        epg_consumption_level = household(
            "monthly_epg_consumption_level", period
        )
        return max_(0, energy_consumption - epg_consumption_level)

from policyengine_uk.model_api import *


class monthly_domestic_energy_consumption(Variable):
    label = "Monthly domestic energy consumption"
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        # From RF "A chilling crisis", p11. Available at https://www.resolutionfoundation.org/app/uploads/2022/08/A-chilling-crisis.pdf
        # This is very approximate but gives us some distribution of seasonal energy consumption at least.
        ENERGY_CONSUMPTION_RATIOS = [
            350,
            350,
            350,
            180,
            180,
            180,
            180,
            180,
            180,
            300,
            300,
            300,
        ]
        consumption_distribution = np.array(ENERGY_CONSUMPTION_RATIOS) / sum(
            ENERGY_CONSUMPTION_RATIOS
        )
        month = period.start.month
        return (
            household("domestic_energy_consumption", period.this_year)
            * consumption_distribution[month - 1]
        )


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


class epg_subsidy(Variable):
    label = "Energy price guarantee subsidy"
    documentation = "Reduction in energy bills due to offsetting the price cap and compensating energy firms."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        total_subsidy = 0
        for month in range(1, MONTHS_IN_YEAR + 1):
            total_subsidy = total_subsidy + household(
                "monthly_epg_subsidy", f"{period.this_year}-{month:02d}"
            )
        return total_subsidy

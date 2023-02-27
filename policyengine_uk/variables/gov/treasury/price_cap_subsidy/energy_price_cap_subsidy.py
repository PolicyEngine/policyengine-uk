from policyengine_uk.model_api import *


class monthly_domestic_energy_consumption(Variable):
    label = "Monthly domestic energy consumption"
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        return (
            household("domestic_energy_consumption", period.this_year)
            / MONTHS_IN_YEAR
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
        relative_change = price_guarantee / price_cap - 1
        discount = -relative_change
        return energy_consumption * discount


class monthly_epg_subsidy(Variable):
    label = "Monthly EPG subsidy"
    entity = Household
    definition_period = MONTH
    value_type = float
    unit = "currency-GBP"
    adds = ["monthly_domestic_energy_consumption"]
    subtracts = ["monthly_epg_consumption_level"]


class energy_price_cap_subsidy(Variable):
    label = "Energy price cap subsidy"
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

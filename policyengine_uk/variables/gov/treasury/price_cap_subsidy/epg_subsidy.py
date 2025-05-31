from policyengine_uk.model_api import *


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

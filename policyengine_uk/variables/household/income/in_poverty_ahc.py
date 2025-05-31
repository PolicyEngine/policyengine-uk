from policyengine_uk.model_api import *


class in_poverty_ahc(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is in absolute poverty, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income_ahc", period)
        threshold = parameters(
            period
        ).household.poverty.absolute_poverty_threshold_ahc
        return income < (threshold * WEEKS_IN_YEAR)

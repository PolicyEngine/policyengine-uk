from policyengine_uk.model_api import *


class in_relative_poverty_ahc(Variable):
    label = "in relative poverty (AHC)"
    entity = Household
    definition_period = YEAR
    value_type = bool

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income_ahc", period)
        # Less than 60% of median income
        median_income = MicroSeries(
            income, weights=household("household_weight", period)
        ).median()
        return income < (median_income * 0.6)

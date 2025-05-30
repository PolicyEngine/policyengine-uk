from policyengine_uk.model_api import *


class in_poverty_bhc(Variable):
    value_type = bool
    entity = Household
    label = (
        "Whether the household is in absolute poverty, before housing costs"
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income", period)
        return income < household("poverty_threshold_bhc", period)

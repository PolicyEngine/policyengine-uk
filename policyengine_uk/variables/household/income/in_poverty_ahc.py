from policyengine_uk.model_api import *


class in_poverty_ahc(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is in absolute poverty, after housing costs"
    documentation = (
        "Absolute poverty: equivalised HBAI net income after housing costs "
        "below the 2010/11 60%-of-median line uprated by CPI "
        "(poverty_threshold_ahc). This is the HBAI absolute low income "
        "measure; the relative measure (60% of the contemporary median) is "
        "in_relative_poverty_ahc."
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income_ahc", period)
        return income < household("poverty_threshold_ahc", period)

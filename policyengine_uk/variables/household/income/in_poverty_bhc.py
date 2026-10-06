from policyengine_uk.model_api import *


class in_poverty_bhc(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is in absolute poverty, before housing costs"
    documentation = (
        "Absolute poverty: equivalised HBAI net income before housing costs "
        "below 60% of the reference-year median held constant in real terms "
        "(poverty_threshold_bhc). The reference year is FYE 2025 from FYE "
        "2022 onward and FYE 2011 before, as in HBAI since March 2026. This "
        "is the HBAI absolute low income "
        "measure; the relative measure (60% of the contemporary median) is "
        "in_relative_poverty_bhc."
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income", period)
        return income < household("poverty_threshold_bhc", period)

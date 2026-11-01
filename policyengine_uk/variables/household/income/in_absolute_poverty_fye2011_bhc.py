from policyengine_uk.model_api import *


class in_absolute_poverty_fye2011_bhc(Variable):
    value_type = bool
    entity = Household
    label = "Whether the household is in absolute poverty on the FYE 2011 reference line, before housing costs"
    documentation = (
        "Equivalised HBAI net income before housing costs below 60% of the FYE "
        "2011 median held constant in real terms "
        "(poverty_threshold_fye2011_bhc), in every year. This is HBAI's "
        "absolute low income measure as published until March 2026; "
        "in_poverty_bhc uses HBAI's current FYE 2025 reference from FYE 2022."
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income", period)
        return income < household("poverty_threshold_fye2011_bhc", period)

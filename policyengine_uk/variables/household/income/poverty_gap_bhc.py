from policyengine_uk.model_api import *


class poverty_gap_bhc(Variable):
    value_type = float
    entity = Household
    label = "Positive financial gap between net household income and the poverty line"
    documentation = (
        "Income is HBAI income before housing costs with a negative figure "
        "reset to zero, as in HBAI, so the gap is at most the poverty line."
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        net_income = household("hbai_household_net_income", period)
        return max_(0, household("poverty_line_bhc", period) - net_income)

from policyengine_uk.model_api import *


class deep_poverty_gap(Variable):
    label = "deep poverty gap"
    documentation = (
        "The financial gap between net household income and the deep poverty "
        "line (before housing costs). Income is HBAI income with a negative "
        "figure reset to zero, so the gap is at most the deep poverty line."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        income = household("hbai_household_net_income", period)
        line = household("deep_poverty_line", period)
        return max_(0, line - income)

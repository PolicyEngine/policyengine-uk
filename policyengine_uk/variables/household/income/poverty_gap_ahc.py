from policyengine_uk.model_api import *


class poverty_gap_ahc(Variable):
    value_type = float
    entity = Household
    label = "Positive financial gap between net household income and the poverty line, after housing costs"
    documentation = (
        "Income is HBAI income after housing costs, derived as in HBAI from "
        "the before-housing-costs income reset to zero. It can be negative, "
        "so the gap can exceed the poverty line by the housing costs."
    )
    definition_period = YEAR

    def formula(household, period, parameters):
        net_income = household("hbai_household_net_income_ahc", period)
        return max_(0, household("poverty_line_ahc", period) - net_income)

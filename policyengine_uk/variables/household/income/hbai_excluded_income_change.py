from policyengine_uk.model_api import *


class hbai_excluded_income_change(Variable):
    label = "Change in HBAI-excluded income"
    documentation = "Effect of policy reforms on HBAI-excluded income"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        hbai_excluded_income = household("hbai_excluded_income", period)
        baseline_hbai_excluded_income = household(
            "baseline_hbai_excluded_income", period
        )
        return hbai_excluded_income - baseline_hbai_excluded_income

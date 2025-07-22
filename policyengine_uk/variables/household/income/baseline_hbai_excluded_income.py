from policyengine_uk.model_api import *


class baseline_hbai_excluded_income(Variable):
    label = "HBAI-excluded income (baseline)"
    documentation = "Total value of income not included in HBAI household net income in the baseline"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        if not parameters(period).household.poverty.exclude_non_hbai_income:
            return 0
        # If baseline policy not viable from the above method,
        # no change in HBAI excluded income
        return household("hbai_excluded_income", period)

from policyengine_uk.model_api import *


class pre_budget_change_household_net_income(Variable):
    label = "household net income"
    documentation = "household net income"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["household_market_income", "pre_budget_change_household_benefits"]
    subtracts = ["pre_budget_change_household_tax"]

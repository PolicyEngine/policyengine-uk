from policyengine_uk.model_api import *


class household_net_income(Variable):
    label = "household net income"
    documentation = "household net income"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "household_market_income",
        "household_benefits",
    ]
    subtracts = [
        "household_tax",
        "pension_contributions",
    ]

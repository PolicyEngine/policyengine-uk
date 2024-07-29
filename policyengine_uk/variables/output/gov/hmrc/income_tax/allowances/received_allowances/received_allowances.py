from policyengine_uk.model_api import *


class received_allowances(Variable):
    value_type = float
    entity = Person
    label = "Total of all allowances received by an individual; minimum value of 0, maximum value of 100% of the individual's income"
    definition_period = YEAR
    unit = GBP

    adds = [
        "received_allowances_earned_income",
        "received_allowances_savings_income",
        "received_allowances_dividend_income",
    ]

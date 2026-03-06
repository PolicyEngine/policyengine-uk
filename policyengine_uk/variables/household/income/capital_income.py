from policyengine_uk.model_api import *


class capital_income(Variable):
    value_type = float
    entity = Person
    label = "Income from savings or dividends"
    definition_period = YEAR
    unit = GBP

    adds = ["savings_interest_income", "dividend_income"]

from policyengine_uk.model_api import *


class taxed_savings_income(Variable):
    value_type = float
    entity = Person
    label = "Savings income which advances the person's income tax schedule"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"
    unit = GBP

    adds = [
        "basic_rate_savings_income",
        "higher_rate_savings_income",
        "add_rate_savings_income",
    ]
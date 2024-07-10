from policyengine_uk.model_api import *


class taxed_income(Variable):
    value_type = float
    entity = Person
    label = "Income which is taxed"
    definition_period = YEAR
    unit = GBP

    adds = [
        "earned_taxable_income",
        "taxed_savings_income",
        "taxed_dividend_income",
    ]
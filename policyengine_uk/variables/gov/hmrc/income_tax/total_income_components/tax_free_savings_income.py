from policyengine_uk.model_api import *


class tax_free_savings_income(Variable):
    value_type = float
    entity = Person
    label = "Income from savings in tax-free accounts"
    definition_period = YEAR
    unit = GBP

    adds = ["individual_savings_account_interest_income"]

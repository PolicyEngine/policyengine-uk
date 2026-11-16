from policyengine_uk.model_api import *


class tax_free_savings_income(Variable):
    value_type = float
    entity = Person
    label = "Income from savings in tax-free accounts"
    definition_period = YEAR
    unit = GBP
    documentation = (
        "Exempt interest additional to ordinary savings interest. Defaults "
        "to ISA interest; a supplied aggregate, including zero, overrides "
        "that default. Market income adds this aggregate once."
    )

    adds = ["individual_savings_account_interest_income"]

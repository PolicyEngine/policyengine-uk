from policyengine_uk.model_api import *


class income_tax_pre_charges(Variable):
    value_type = float
    entity = Person
    label = "Income Tax before any tax charges"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 23"
    unit = GBP

    adds = [
        "earned_income_tax",
        "savings_income_tax",
        "dividend_income_tax",
    ]
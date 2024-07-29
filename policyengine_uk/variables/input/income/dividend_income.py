from policyengine_uk.model_api import *


class dividend_income(Variable):
    label = "dividend income"
    documentation = "Income from dividends on shares."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

from policyengine_uk.model_api import *


class dividend_income(Variable):
    value_type = float
    entity = Person
    label = "dividend income"
    documentation = "Total income from dividends, gross of tax"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(b-d)"
    unit = GBP
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

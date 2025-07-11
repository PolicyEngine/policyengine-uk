from policyengine_uk.model_api import *


class property_income(Variable):
    value_type = float
    entity = Person
    label = "rental income"
    documentation = "Income from rental of property"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(b)"
    unit = GBP
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

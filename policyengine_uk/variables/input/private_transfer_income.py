from policyengine_uk.model_api import *


class private_transfer_income(Variable):
    value_type = float
    entity = Person
    label = "private transfer income"
    documentation = "Income from private transfers"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

from policyengine_uk.model_api import *


class lump_sum_income(Variable):
    value_type = float
    entity = Person
    label = "lump sum income"
    documentation = "Income from lump sums"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

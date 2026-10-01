from policyengine_uk.model_api import *


class consumer_debt(Variable):
    label = "consumer debt"
    documentation = "Outstanding non-mortgage, non-student-loan borrowing (personal loans, credit, hire purchase), imputed from the Wealth and Assets Survey"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK
    default_value = 0

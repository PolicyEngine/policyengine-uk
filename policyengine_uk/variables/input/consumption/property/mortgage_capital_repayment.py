from policyengine_uk.model_api import *


class mortgage_capital_repayment(Variable):
    value_type = float
    entity = Household
    label = "mortgage capital repayments"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

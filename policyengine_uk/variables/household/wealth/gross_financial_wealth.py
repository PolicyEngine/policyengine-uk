from policyengine_uk.model_api import *


class gross_financial_wealth(Variable):
    label = "Gross financial wealth"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

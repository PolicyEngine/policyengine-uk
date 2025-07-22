from policyengine_uk.model_api import *


class net_financial_wealth(Variable):
    label = "Net financial wealth"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"

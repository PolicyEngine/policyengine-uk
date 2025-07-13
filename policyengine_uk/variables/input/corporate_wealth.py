from policyengine_uk.model_api import *


class corporate_wealth(Variable):
    label = "corporate wealth"
    documentation = "Total owned wealth in corporations"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK

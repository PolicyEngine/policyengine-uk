from policyengine_uk.model_api import *


class mortgage_debt(Variable):
    label = "mortgage debt"
    documentation = "Outstanding debt secured on UK land or property (mortgages and secured loans), imputed from the Wealth and Assets Survey"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK
    default_value = 0

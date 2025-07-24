from policyengine_uk.model_api import *

# The below variables follow the COICOP MECE categories.


class health_consumption(Variable):
    entity = Household
    label = "health consumption"
    documentation = "Total yearly expenditure on health"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

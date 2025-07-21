from policyengine_uk.model_api import *

# The below variables follow the COICOP MECE categories.


class alcohol_and_tobacco_consumption(Variable):
    entity = Household
    label = "alcohol and tobacco consumption"
    documentation = "Total yearly expenditure on alcohol and tobacco"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

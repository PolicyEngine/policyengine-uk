from policyengine_uk.model_api import *

# The below variables follow the COICOP MECE categories.


class clothing_and_footwear_consumption(Variable):
    entity = Household
    label = "clothing and footwear consumption"
    documentation = "Total yearly expenditure on clothing and footwear"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

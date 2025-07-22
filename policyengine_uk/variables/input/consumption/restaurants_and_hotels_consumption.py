from policyengine_uk.model_api import *

# The below variables follow the COICOP MECE categories.


class restaurants_and_hotels_consumption(Variable):
    entity = Household
    label = "restaurants and hotels consumption"
    documentation = "Total yearly expenditure on restaurants and hotels"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

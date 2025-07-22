from policyengine_uk.model_api import *

# The below variables follow the COICOP MECE categories.


class diesel_spending(Variable):
    label = "diesel consumption"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

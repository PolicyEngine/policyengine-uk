from policyengine_uk.model_api import *

# The below variables follow the COICOP MECE categories.


class miscellaneous_consumption(Variable):
    entity = Household
    label = "miscellaneous consumption"
    documentation = "Total yearly expenditure on miscellaneous goods"
    unit = GBP
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    uprating = "gov.obr.consumer_price_index"

from policyengine_uk.model_api import *


class bus_fare_spending_reported(Variable):
    label = "bus fare spending reported"
    documentation = "Reported household bus and coach spending, retained as the fallback when usable journey data is absent."
    entity = Household
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

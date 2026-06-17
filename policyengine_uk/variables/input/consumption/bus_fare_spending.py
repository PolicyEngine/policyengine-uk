from policyengine_uk.model_api import *

# COICOP 7.3.2 (passenger transport by road: bus & coach fares). A
# sub-component of transport_consumption, imputed separately from LCFS by
# policyengine-uk-data so bus fare reforms can be modelled. Not added into the
# `consumption` total, which already counts it via transport_consumption.


class bus_fare_spending(Variable):
    label = "bus and coach fare spending"
    documentation = "Household spending on bus and coach fares (COICOP 7.3.2)."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

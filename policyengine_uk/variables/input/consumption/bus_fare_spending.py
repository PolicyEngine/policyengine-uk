from policyengine_uk.model_api import *

# COICOP 7.3.2 (passenger transport by road: bus & coach fares). A
# sub-component of transport_consumption, imputed separately from LCFS by
# policyengine-uk-data so bus fare reforms can be modelled. Not added into the
# `consumption` total, which already counts it via transport_consumption.


class bus_fare_spending(Variable):
    label = "bus and coach fare spending"
    documentation = (
        "Household bus fares summed from each person's journeys where supplied. "
        "Without journey data, retains reported bus and coach spending "
        "(COICOP 7.3.2), allocated across people by age. Already included in "
        "transport_consumption; do not add it to consumption again."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    adds = ["person_bus_fare_spending"]

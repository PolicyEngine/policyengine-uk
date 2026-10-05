from policyengine_uk.model_api import *


class bus_in_london_trips(Variable):
    label = "bus in london trips"
    documentation = (
        "Annual local-bus trips on the bus-in-London series, supplied by the dataset."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW

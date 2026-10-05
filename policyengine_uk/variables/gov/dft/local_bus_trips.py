from policyengine_uk.model_api import *


class local_bus_trips(Variable):
    label = "annual local bus trips"
    documentation = (
        "Total trips across the two local-bus series; may also be supplied directly "
        "when the series split is unavailable. Supply bus_pass_eligible alongside "
        "journeys: the model does not infer statutory pass eligibility and a "
        "missing flag defaults to paying fares."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW
    adds = ["bus_in_london_trips", "other_local_bus_trips"]

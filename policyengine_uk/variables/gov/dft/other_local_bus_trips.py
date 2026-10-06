from policyengine_uk.model_api import *


class other_local_bus_trips(Variable):
    label = "other local bus trips"
    documentation = (
        "Annual local-bus trips on the other-local-bus series, supplied by the dataset. "
        "Supply bus_pass_eligible alongside journeys: the model does not infer "
        "statutory pass eligibility and a missing flag defaults to paying fares."
    )
    entity = Person
    definition_period = YEAR
    value_type = float
    quantity_type = FLOW

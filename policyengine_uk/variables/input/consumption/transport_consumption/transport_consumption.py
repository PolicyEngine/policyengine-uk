from policyengine_uk.model_api import *


class transport_consumption(Variable):
    label = "transport consumption"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    adds = [
        "petrol_consumption",
        "diesel_consumption",
        "other_transport_consumption",
    ]

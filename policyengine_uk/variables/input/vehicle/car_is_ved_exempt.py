from policyengine_uk.model_api import *


class car_is_ved_exempt(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "Car has a vehicle excise duty exemption"
    unit = "/1"

from policyengine_uk.model_api import *


class vehicle_excise_duty(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Vehicle excise duty on household cars"
    unit = GBP
    adds = ["car_vehicle_excise_duty"]

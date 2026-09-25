from policyengine_uk.model_api import *


class CarFuelType(Enum):
    PETROL = "Petrol"
    DIESEL_RDE2 = "Diesel meeting RDE2"
    DIESEL_NON_RDE2 = "Diesel not meeting RDE2"
    ALTERNATIVE_FUEL = "Alternative fuel, including hybrid and LPG"
    ELECTRIC = "Electric or other zero emission"


class car_fuel_type(Variable):
    value_type = Enum
    possible_values = CarFuelType
    default_value = CarFuelType.PETROL
    entity = Person
    definition_period = YEAR
    label = "Car fuel type"

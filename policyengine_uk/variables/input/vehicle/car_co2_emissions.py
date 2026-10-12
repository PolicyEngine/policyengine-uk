from policyengine_uk.model_api import *


class car_co2_emissions(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Car CO2 emissions in grams per kilometre"
    unit = "g/km"
    quantity_type = STOCK

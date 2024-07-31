from policyengine_uk.model_api import *


class housing_water_and_electricity_consumption(Variable):
    label = "housing, water and electricity consumption"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    adds = [
        "rent",
        "water_charges",
        "domestic_energy_consumption",
    ]

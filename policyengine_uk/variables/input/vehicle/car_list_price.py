from policyengine_uk.model_api import *


class car_list_price(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Car list price when first registered"
    unit = GBP
    quantity_type = STOCK

from policyengine_uk.model_api import *


class car_engine_size(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR
    label = "Car engine capacity in cubic centimetres"
    unit = "cubic_centimetre"
    quantity_type = STOCK

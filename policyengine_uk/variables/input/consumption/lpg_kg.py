from policyengine_uk.model_api import *


class lpg_kg(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Annual kilograms of lpg used as road fuel"
    unit = "kilogram"

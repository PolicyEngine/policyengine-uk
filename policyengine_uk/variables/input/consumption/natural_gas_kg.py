from policyengine_uk.model_api import *


class natural_gas_kg(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Annual kilograms of natural gas used as road fuel"
    unit = "kilogram"

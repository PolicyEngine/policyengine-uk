from policyengine_uk.model_api import *


class wine_litres(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Annual litres of wine"
    unit = "litre"

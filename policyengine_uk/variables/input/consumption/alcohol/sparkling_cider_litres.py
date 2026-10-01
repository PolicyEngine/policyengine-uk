from policyengine_uk.model_api import *


class sparkling_cider_litres(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Annual litres of sparkling cider"
    unit = "litre"

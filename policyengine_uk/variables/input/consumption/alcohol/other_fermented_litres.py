from policyengine_uk.model_api import *


class other_fermented_litres(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Annual litres of other fermented"
    unit = "litre"

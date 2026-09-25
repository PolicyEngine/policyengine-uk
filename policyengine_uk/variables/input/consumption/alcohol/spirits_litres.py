from policyengine_uk.model_api import *


class spirits_litres(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
    label = "Annual litres of spirits"
    unit = "litre"

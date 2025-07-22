from policyengine_uk.model_api import *


class ssmg_reported(Variable):
    label = "Sure Start Maternity Grant (reported)"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

from policyengine_uk.model_api import *


class ssmg(Variable):
    label = "Sure Start Maternity Grant"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = ["ssmg_reported"]

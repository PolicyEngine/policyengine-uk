from policyengine_uk.model_api import *


class benunit_tax(Variable):
    value_type = float
    entity = ben_unit
    label = "Benefit unit tax paid"
    definition_period = YEAR
    unit = GBP

    adds = ["tax"]

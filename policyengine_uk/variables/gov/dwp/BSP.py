from policyengine_uk.model_api import *


class BSP(Variable):
    value_type = float
    entity = Person
    label = "Bereavement Support Payment"
    definition_period = YEAR
    unit = GBP

    adds = ["BSP_reported"]


class BSP_reported(Variable):
    value_type = float
    entity = Person
    label = "Bereavement Support Payment (reported)"
    definition_period = YEAR
    unit = GBP

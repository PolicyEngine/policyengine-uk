from policyengine_uk.model_api import *


class bsp(Variable):
    value_type = float
    entity = Person
    label = "Bereavement Support Payment"
    definition_period = YEAR
    unit = GBP

    adds = ["bsp_reported"]

from policyengine_uk.model_api import *


class bsp(Variable):
    value_type = float
    entity = Person
    label = "Bereavement Support Payment"
    definition_period = YEAR
    unit = GBP

    adds = ["bsp_reported"]


class bsp_reported(Variable):
    value_type = float
    entity = Person
    label = "Bereavement Support Payment (reported)"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.consumer_price_index"

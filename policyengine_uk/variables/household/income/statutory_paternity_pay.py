from policyengine_uk.model_api import *
import datetime
import numpy as np


class statutory_paternity_pay(Variable):
    label = "Statutory paternity pay"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.consumer_price_index"

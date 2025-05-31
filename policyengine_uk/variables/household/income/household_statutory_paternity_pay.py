from policyengine_uk.model_api import *
import datetime
import numpy as np


class household_statutory_paternity_pay(Variable):
    label = "Statutory paternity pay"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

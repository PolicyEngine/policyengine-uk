from policyengine_uk.model_api import *
import datetime
import numpy as np


class capital_gains(Variable):
    label = "capital gains"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.obr.non_labour_income"
    adds = [
        "capital_gains_before_response",
        "capital_gains_behavioural_response",
    ]

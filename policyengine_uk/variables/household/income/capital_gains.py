from policyengine_uk.model_api import *
import datetime
import numpy as np


class capital_gains(Variable):
    label = "capital gains"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    adds = [
        "capital_gains_before_response",
        "capital_gains_behavioural_response",
    ]

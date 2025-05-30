from policyengine_uk.model_api import *
import datetime
import numpy as np


class base_net_income(Variable):
    value_type = float
    entity = Person
    label = "Existing net income for the person to use as a base in microsimulation"
    definition_period = YEAR
    unit = GBP

from policyengine_uk.model_api import *
import datetime
import numpy as np


class hours_worked(Variable):
    value_type = float
    entity = Person
    label = "Hours worked per week"
    definition_period = YEAR
    unit = "hour"

from policyengine_uk.model_api import *
import datetime
import numpy as np


class weekly_hours(Variable):
    value_type = float
    entity = Person
    label = "Weekly hours"
    documentation = "Average weekly hours worked"
    definition_period = YEAR
    unit = "hour"
    quantity_type = FLOW

    def formula(person, period, parameters):
        return person("hours_worked", period) / WEEKS_IN_YEAR

from policyengine_uk.model_api import *
import datetime
import numpy as np


class in_work(Variable):
    value_type = bool
    entity = Person
    label = "Worked some hours"
    definition_period = YEAR

    def formula(person, period, parameters):
        has_hours_worked = person("hours_worked", period) > 0
        earnings = add(
            person, period, ["employment_income", "self_employment_income"]
        )
        has_earnings = earnings > 0
        return has_hours_worked | has_earnings

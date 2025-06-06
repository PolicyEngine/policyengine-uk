from policyengine_uk.model_api import *
import datetime
import numpy as np


class earned_income(Variable):
    value_type = float
    entity = Person
    label = "Total earned income"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "private_pension_income",
        ]
        return add(person, period, COMPONENTS)

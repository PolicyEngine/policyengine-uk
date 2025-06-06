from policyengine_uk.model_api import *
import datetime
import numpy as np


class household_gross_income(Variable):
    value_type = float
    entity = Household
    unit = GBP
    label = "Household gross income"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        return add(
            household,
            period,
            ["household_market_income", "household_benefits"],
        )

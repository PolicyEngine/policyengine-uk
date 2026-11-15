from policyengine_uk.model_api import *
import numpy as np


class real_household_net_income_ahc(Variable):
    label = "real household net income after housing costs (base-year prices)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        net_income = household("household_net_income_ahc", period)
        return net_income * household("inflation_adjustment", period)

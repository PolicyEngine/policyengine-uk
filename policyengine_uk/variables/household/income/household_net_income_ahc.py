from policyengine_uk.model_api import *
import datetime
import numpy as np


class household_net_income_ahc(Variable):
    label = "household net income"
    documentation = "household net income"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "household_market_income",
        "household_benefits",
    ]
    subtracts = [
        "household_tax",
        "housing_costs",
    ]

    def formula(household, period, parameters):
        market_income = household("household_market_income", period)
        benefits = household("household_benefits", period)
        tax = household("household_tax", period)
        housing_costs = household("housing_costs", period)
        return np.round(market_income + benefits - tax - housing_costs)

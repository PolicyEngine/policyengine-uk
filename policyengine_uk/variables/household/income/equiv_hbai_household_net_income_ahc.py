from policyengine_uk.model_api import *
import datetime
import numpy as np


class equiv_hbai_household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = "Equivalised household net income, after housing costs (HBAI)"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        income = household("hbai_household_net_income_ahc", period)
        equivalisation = household("household_equivalisation_ahc", period)
        return income / equivalisation

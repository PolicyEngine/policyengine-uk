from policyengine_uk.model_api import *
import datetime
import numpy as np


class equiv_hbai_household_net_income(Variable):
    value_type = float
    entity = Household
    label = "Equivalised household net income (HBAI)"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        income = household("hbai_household_net_income", period)
        equivalisation = household("household_equivalisation_bhc", period)
        return income / equivalisation

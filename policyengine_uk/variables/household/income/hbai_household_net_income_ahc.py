from policyengine_uk.model_api import *
import datetime
import numpy as np


class hbai_household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = "Household net income, after housing costs"
    definition_period = YEAR
    unit = GBP

    adds = ["hbai_household_net_income"]
    subtracts = [
        "rent",
        "water_and_sewerage_charges",
        "mortgage_interest_repayment",
        "structural_insurance_payments",
    ]


class real_hbai_household_net_income_ahc(Variable):
    label = "real household net income after housing costs (HBAI definition)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return household("hbai_household_net_income_ahc", period) * household(
            "inflation_adjustment_ahc", period
        )

from policyengine_uk.model_api import *
import datetime
import numpy as np


class hbai_household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = "Household net income, after housing costs"
    documentation = (
        "HBAI household net income after housing costs. As in HBAI, it is "
        "derived from the before-housing-costs income after a negative figure "
        'has been reset to zero, and it can itself be negative: "negative AHC '
        'incomes calculated from the adjusted BHC incomes are possible".'
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#negative-incomes"

    # The reset before-housing-costs income, not
    # hbai_household_net_income_before_reset_to_zero.
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
            "inflation_adjustment", period
        )

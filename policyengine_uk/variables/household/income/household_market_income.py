from policyengine_uk.model_api import *
import datetime
import numpy as np


class household_market_income(Variable):
    value_type = float
    entity = Household
    label = "household market income"
    documentation = "Market income for the household"
    definition_period = YEAR
    unit = GBP
    adds = [
        "employment_income",
        "self_employment_income",
        "savings_interest_income",
        "dividend_income",
        "miscellaneous_income",
        "property_income",
        "private_pension_income",
        "private_transfer_income",
        "maintenance_income",
        "capital_gains",
    ]

    def formula(person, period, parameters):
        total = add(person, period, household_market_income.adds)
        contrib = parameters(
            period
        ).gov.contrib.policyengine.economy.gdp_per_capita
        return total * (contrib + 1)

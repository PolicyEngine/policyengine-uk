from policyengine_uk.model_api import *
import datetime
import numpy as np


HOUSEHOLD_MARKET_INCOME_VARIABLES = [
    "employment_income",
    "self_employment_income",
    "savings_interest_income",
    "tax_free_savings_income",
    "individual_savings_account_dividend_income",
    "dividend_income",
    "miscellaneous_income",
    # Landlords' profit after mortgage interest, as in HBAI income.
    "property_income_after_finance_costs",
    "private_pension_income",
    "private_transfer_income",
    "maintenance_income",
    "capital_gains",
]


class household_market_income(Variable):
    value_type = float
    entity = Household
    label = "household market income"
    documentation = "Market income for the household"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        # Trading losses are negative self-employment income.
        total = add(person, period, HOUSEHOLD_MARKET_INCOME_VARIABLES) - add(
            person, period, ["trading_loss"]
        )
        contrib = parameters(period).gov.contrib.policyengine.economy.gdp_per_capita
        return total * (contrib + 1)

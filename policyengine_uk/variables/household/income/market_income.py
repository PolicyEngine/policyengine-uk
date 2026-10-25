from policyengine_uk.model_api import *
import datetime
import numpy as np


class market_income(Variable):
    value_type = float
    entity = Person
    label = "Market income"
    documentation = "Income from market sources"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        INCOME_VARIABLES = [
            "employment_income",
            "self_employment_income",
            "savings_interest_income",
            "dividend_income",
            "miscellaneous_income",
            # Landlords' profit after mortgage interest, as in HBAI income.
            "property_income_after_finance_costs",
            "private_pension_income",
            "private_transfer_income",
            "maintenance_income",
            "spousal_maintenance_income",
        ]
        income = add(person, period, INCOME_VARIABLES)
        return (
            income
            - person("trading_loss", period)
            - person("maintenance_expenses", period)
        )

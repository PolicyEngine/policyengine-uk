from policyengine_uk.model_api import *
import datetime
import numpy as np


class hbai_household_net_income(Variable):
    value_type = float
    entity = Household
    label = "Household net income (HBAI definition)"
    documentation = "Disposable income for the household, following the definition used for official poverty statistics"
    unit = GBP
    definition_period = YEAR

    adds = [
        "household_market_income",
        "child_benefit",
        "esa_income",
        "esa_contrib",
        "housing_benefit",
        "income_support",
        "jsa_income",
        "jsa_contrib",
        "pension_credit",
        "universal_credit",
        "working_tax_credit",
        "child_tax_credit",
        "attendance_allowance",
        "afcs",
        "bsp",
        "carers_allowance",
        "dla",
        "iidb",
        "incapacity_benefit",
        "jsa_contrib",
        "pip",
        "sda",
        "state_pension",
        "maternity_allowance",
        "statutory_sick_pay",
        "statutory_maternity_pay",
        "ssmg",
        "basic_income",
        "cost_of_living_support_payment",
        "winter_fuel_allowance",
        "tax_free_childcare",
        # Reference for tax-free-childcare: https://assets.publishing.service.gov.uk/media/5e7b191886650c744175d08b/households-below-average-income-1994-1995-2018-2019.pdf
    ]
    subtracts = [
        "council_tax",
        "domestic_rates",
        "wealth_tax",
        "income_tax",
        "national_insurance",
    ]


class real_hbai_household_net_income(Variable):
    label = "real household net income (HBAI definition)"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return household("hbai_household_net_income", period) * household(
            "inflation_adjustment", period
        )

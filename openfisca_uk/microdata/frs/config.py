from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *
from openfisca_uk.microdata.frs.frs_variables import FRS_variables


class employment_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from employment'
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(a)"

    def formula(person, period, parameters):
        return person("P_UGRSPAY", period, options=[ADD])

class pension_contributions(Variable):
    value_type = float
    entity = Person
    label = u'Amount contributed to registered pension schemes paid by the individual (not the employer)'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_UDEDUC1", period, options=[ADD])

class pension_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from pensions'
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"

    def formula(person, period, parameters):
        return person("P_INPENINC", period, options=[ADD])

class trading_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from trading profits'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(a)"

    def formula(person, period, parameters):
        return person("P_PROFIT1", period, options=[ADD]) * (person("P_PROFIT2", period.first_week) == 1)

class trading_loss(Variable):
    value_type = float
    entity = Person
    label = u'Loss from trading in the current year.'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_PROFIT1", period, options=[ADD]) * (person("P_PROFIT2", period.first_week) == 2)

class savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from interest on savings'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(a)"

    def formula(person, period, parameters):
        SAVINGS_ACCOUNT_CODES = [
            1,
            2,
            3,
            4,
            5,
            6,
            10,
            11,
            12,
            14,
            16,
            17,
            18,
            19,
            21,
            25,
            26,
            27,
            28,
            29,
            30
        ]
        savings_accounts = [f"P_ACCINT_ACCOUNT_CODE_{i}" for i in SAVINGS_ACCOUNT_CODES]
        return add(person, period, savings_accounts, options=[ADD])

class tax_free_savings_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from savings in tax-free accounts'
    definition_period = YEAR

    def formula(person, period, parameters):
        TAX_FREE_SAVINGS_ACCOUNT_CODES = [
            6,
            14,
            21,
        ]
        accounts = [f"P_ACCINT_ACCOUNT_CODE_{i}" for i in TAX_FREE_SAVINGS_ACCOUNT_CODES]
        return add(person, period, accounts, options=[ADD])

class dividend_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from dividends'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(b-d)"

    def formula(person, period, parameters):
        DIVIDEND_ACCOUNT_CODES = [
            7,
            8,
            9,
            13,
            22,
            23,
            24
        ]
        dividend_accounts = [f"P_ACCINT_ACCOUNT_CODE_{i}" for i in DIVIDEND_ACCOUNT_CODES]
        return add(person, period, dividend_accounts, options=[ADD])

class sublet_income(Variable):
    value_type = float
    entity = Person
    label = u'Income received from sublet agreements'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("H_SUBLET", period, options=[ADD])

class tax_reported(Variable):
    value_type = float
    entity = Person
    label = u'Reported tax paid'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_INDINC", period, options=[ADD]) - person("P_NINDINC", period, options=[ADD])

class base_net_income(Variable):
    value_type = float
    entity = Person
    label = u'Existing net income for the person to use as a base in microsimulation'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_NINDINC", period, options=[ADD])


input_variables = [
    employment_income,
    pension_contributions,
    pension_income,
    trading_income,
    savings_interest_income,
    dividend_income,
    tax_free_savings_income,
    sublet_income,
    tax_reported,
    base_net_income
]


class from_FRS(Reform):
    def apply(self):
        for var in FRS_variables:
            self.add_variable(var)
        for var in input_variables:
            self.update_variable(var)

from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

# FRS variables

class P_GROSS4(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class B_GROSS4(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR

class H_GROSS4(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR

class P_UGRSPAY(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_INPENINC(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

class P_PROFIT1(Variable):
    value_type = float
    entity = Person
    definition_period = WEEK

# Input variables

class employment_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from employment'
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(a)"

    def formula(person, period, parameters):
        return person("P_UGRSPAY", period, options=[ADD])

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
        return person("P_PROFIT1", period, options=[ADD])

FRS_variables = [
    P_GROSS4, 
    B_GROSS4, 
    H_GROSS4,
    P_UGRSPAY,
    P_INPENINC,
    P_PROFIT1,
]
input_variables = [
    employment_income,
    pension_income,
    trading_income,
]


class from_FRS(Reform):
    def apply(self):
        for var in FRS_variables:
            self.add_variable(var)
        for var in input_variables:
            self.update_variable(var)

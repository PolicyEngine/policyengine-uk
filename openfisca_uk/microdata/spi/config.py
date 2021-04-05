from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

# SPI Variables

class PAY(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class EXPS(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class PENSION(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class SRP(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class INCPBEN(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class UBISJA(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class OSSBEN(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class PROFITS(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class INCPROP(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class INCBBS(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class DIVIDENDS(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class OTHERINV(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class OTHERINC(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class MOTHINC(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class BPADUE(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class MCAS(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class FACT(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class TAXINC(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class TOTTAX(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class SCOT_TXP(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

# Input variables

class pays_scottish_income_tax(Variable):
    value_type = float
    entity = Person
    label = u'Whether the individual pays Scottish Income Tax rates'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("SCOT_TXP", period) == 1

class employment_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from employment'
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(a)"

    def formula(person, period, parameters):
        return person("PAY", period) + person("EXPS", period)

class pension_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from pensions'
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"

    def formula(person, period, parameters):
        return person("PENSION", period)

class social_security_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from social security'
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"

    def formula(person, period, parameters):
        BENEFITS = [
            "SRP",
            "INCPBEN",
            "UBISJA",
            "OSSBEN"
        ]

class trading_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from trading profits'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(a)"

    def formula(person, period, parameters):
        return person("PROFITS", period)

class property_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from rental of property'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(b)"

    def formula(person, period, parameters):
        return person("INCPROP", period)

class savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from interest on savings'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(a)"

    def formula(person, period, parameters):
        return person("INCBBS", period)

class dividend_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from dividends'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(b-d)"

    def formula(person, period, parameters):
        return person("DIVIDENDS", period)

class miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = u'Income from other sources'
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 574(1)"

    def formula(person, period, parameters):
        other_fields = [
            "OTHERINV",
            "OTHERINC",
            "MOTHINC"
        ]
        return add(person, period, other_fields)

class blind_persons_allowance(Variable):
    value_type = float
    entity = Person
    label = u'Blind Person\'s Allowance for the year (not simulated)'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 38"

    def formula(person, period, parameters):
        return person("BPADUE", period)


class marriage_allowance(Variable):
    value_type = float
    entity = Person
    label = u'Marriage Allowance for the year'
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 55"

    def formula(person, period, parameters):
        return person("MCAS", period)

SPI_variables = [
    PAY,
    EXPS,
    PENSION,
    SRP,
    INCPBEN,
    UBISJA,
    OSSBEN,
    PROFITS,
    INCPROP,
    INCBBS,
    DIVIDENDS,
    OTHERINV,
    OTHERINC,
    MOTHINC,
    BPADUE,
    MCAS,
    FACT,
    SCOT_TXP,
    TAXINC,
    TOTTAX,
]

input_variables = [
    employment_income,
    pension_income,
    social_security_income,
    trading_income,
    property_income,
    savings_interest_income,
    dividend_income,
    miscellaneous_income,
    blind_persons_allowance,
    marriage_allowance,
    pays_scottish_income_tax
]


class from_SPI(Reform):
    def apply(self):
        for var in SPI_variables:
            self.add_variable(var)
        for var in input_variables:
            self.update_variable(var)

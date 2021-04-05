from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

# SPI Variables

class PAY(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class TAXTERM(Variable):
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

class GIFTAID(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class GIFTINV(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class CAPALL(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class COVNTS(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class DEFICIEN(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class EPB(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class MOTHDED(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR

class PENSRLF(Variable):
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
        return person("PAY", period) + person("EPB", period) + person("TAXTERM", period)

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
        return add(person, period, BENEFITS)

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


class married_couples_allowance(Variable):
    value_type = float
    entity = Person
    label = u'Married Couples\' allowance for the year'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("MCAS", period)

class gift_aid(Variable):
    value_type = float
    entity = Person
    label = u'Expenditure under Gift Aid'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("GIFTAID", period)


class capital_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = u'Deduction from capital expenditure allowances'
    definition_period = YEAR
    reference = "Capital Allowances Act 2001 s. 1"

    def formula(person, period, parameters):
        return person("CAPALL", period)

class deficiency_relief(Variable):
    value_type = float
    entity = Person
    label = u'Deficiency relief'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("DEFICIEN", period)

class covenanted_payments(Variable):
    value_type = float
    entity = Person
    label = u'Covenanted payments to charities'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("COVNTS", period)

class charitable_investment_gifts(Variable):
    value_type = float
    entity = Person
    label = u'Gifts of qualifying investment or property to charities'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("GIFTINV", period)

class employment_expenses(Variable):
    value_type = float
    entity = Person
    label = u'Cost of expenses necessarily incurred and reimbursed by employment'
    definition_period = YEAR
    reference = "Income Tax Act (Earnings and Pensions) Act 2003 s. 333"

    def formula(person, period, parameters):
        return person("EPB", period)

class other_deductions(Variable):
    value_type = float
    entity = Person
    label = u'All other tax deductions'
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("MOTHDED", period)

class pension_contributions_relief(Variable):
    value_type = float
    entity = Person
    label = u'Tax relief from pension contributions'
    definition_period = YEAR
    reference = "Finance Act 2004 s. 188-194"

    def formula(person, period, parameters):
        return person("PENSRLF", period)


SPI_variables = [
    PAY,
    TAXTERM,
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
    GIFTAID,
    GIFTINV,
    CAPALL,
    COVNTS,
    DEFICIEN,
    EPB,
    MOTHDED,
    PENSRLF,
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
    married_couples_allowance,
    pays_scottish_income_tax,
    gift_aid,
    deficiency_relief,
    covenanted_payments,
    charitable_investment_gifts,
    other_deductions,
    pension_contributions_relief,
    capital_allowance_deduction
]


class from_SPI(Reform):
    def apply(self):
        for var in SPI_variables:
            self.add_variable(var)
        for var in input_variables:
            self.update_variable(var)

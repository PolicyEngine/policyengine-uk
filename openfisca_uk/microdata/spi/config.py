from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *
from openfisca_uk.microdata.spi.spi_variables import SPI_variables

# Input variables


class age(Variable):
    value_type = float
    entity = Person
    label = u"The age of the person in years"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        LOWER = np.array([16, 25, 35, 45, 55, 65, 75])
        UPPER = np.array([25, 35, 45, 55, 65, 75, 80])
        age_range = person("AGERANGE", period) - 1
        sampled_age = LOWER[age_range] + random(person) * (
            UPPER[age_range] - LOWER[age_range]
        )
        return sampled_age


class pays_scottish_income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Whether the individual pays Scottish Income Tax rates"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("SCOT_TXP", period) == 1


class employment_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from employment"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(a)"

    def formula(person, period, parameters):
        return (
            person("PAY", period)
            + person("EPB", period)
            + person("TAXTERM", period)
        )


class pension_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from pensions"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"

    def formula(person, period, parameters):
        return person("PENSION", period)


class social_security_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from social security"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"

    def formula(person, period, parameters):
        BENEFITS = ["SRP", "INCPBEN", "UBISJA", "OSSBEN"]
        return add(person, period, BENEFITS)


class trading_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from trading profits"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(a)"

    def formula(person, period, parameters):
        return person("PROFITS", period)


class property_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from rental of property"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(b)"

    def formula(person, period, parameters):
        return person("INCPROP", period)


class savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from interest on savings"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(a)"

    def formula(person, period, parameters):
        return person("INCBBS", period)


class dividend_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from dividends"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(b-d)"

    def formula(person, period, parameters):
        return person("DIVIDENDS", period)


class miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from other sources"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 574(1)"

    def formula(person, period, parameters):
        other_fields = ["OTHERINV", "OTHERINC", "MOTHINC"]
        return add(person, period, other_fields)


class blind_persons_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Blind Person's Allowance for the year (not simulated)"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 38"

    def formula(person, period, parameters):
        return person("BPADUE", period)


class married_couples_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Married Couples' allowance for the year"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("MCAS", period)


class gift_aid(Variable):
    value_type = float
    entity = Person
    label = u"Expenditure under Gift Aid"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("GIFTAID", period)


class capital_allowances(Variable):
    value_type = float
    entity = Person
    label = u"Full relief from capital expenditure allowances"
    definition_period = YEAR
    reference = "Capital Allowances Act 2001 s. 1"

    def formula(person, period, parameters):
        return person("CAPALL", period)


class deficiency_relief(Variable):
    value_type = float
    entity = Person
    label = u"Deficiency relief"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("DEFICIEN", period)


class covenanted_payments(Variable):
    value_type = float
    entity = Person
    label = u"Covenanted payments to charities"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("COVNTS", period)


class charitable_investment_gifts(Variable):
    value_type = float
    entity = Person
    label = u"Gifts of qualifying investment or property to charities"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("GIFTINV", period)


class employment_expenses(Variable):
    value_type = float
    entity = Person
    label = (
        u"Cost of expenses necessarily incurred and reimbursed by employment"
    )
    definition_period = YEAR
    reference = "Income Tax Act (Earnings and Pensions) Act 2003 s. 333"

    def formula(person, period, parameters):
        return person("EPB", period)


class other_deductions(Variable):
    value_type = float
    entity = Person
    label = u"All other tax deductions"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("MOTHDED", period)


class pension_contributions(Variable):
    value_type = float
    entity = Person
    label = u"Amount contributed to registered pension schemes paid by the individual (not the employer)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("PENSRLF", period)


class person_weight(Variable):
    value_type = float
    entity = Person
    label = u"Weight factor for the person"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_FACT", period)


class benunit_weight(Variable):
    value_type = float
    entity = BenUnit
    label = u"Weight factor for the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("B_FACT", period)


class household_weight(Variable):
    value_type = float
    entity = Household
    label = u"Weight factor for the household"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("H_FACT", period)


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
    pension_contributions,
    capital_allowances,
    person_weight,
    benunit_weight,
    household_weight,
    age,
]


class from_SPI(Reform):
    def apply(self):
        for var in SPI_variables:
            self.add_variable(var)
        for var in input_variables:
            self.update_variable(var)

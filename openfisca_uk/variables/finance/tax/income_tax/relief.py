from openfisca_uk.tools.general import *
from openfisca_uk.entities import *

"""
These variables calculate the tax reliefs that a taxpayer is eligible for, following the Income Tax Act (2007) s. 23.
Tax reliefs are amounts to be deducted from the assessed total income of a person.
The section detailing some tax reliefs applicable is section 24 of the Act, but others are described in the 2003 and 2005 Acts as deductions from the respective components.
Not all reliefs are calculated here - only the major ones.
"""

# Employment income


class taxable_employment_income(Variable):
    value_type = float
    entity = Person
    label = u"Net taxable earnings"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 11"

    def formula(person, period, parameters):
        taxable_earnings = person("employment_income", period)
        deductions = add(
            person, period, ["employment_deductions", "pension_contributions"]
        )
        benefits = person("employment_benefits", period)
        return max_(0, taxable_earnings + benefits - deductions)


class employment_benefits(Variable):
    value_type = float
    entity = Person
    label = u"Employment benefits"
    definition_period = YEAR

    def formula(person, period, parameters):
        return add(person, period, ["SSP", "SMP"])


class SMP(Variable):
    value_type = float
    entity = Person
    label = u"SMP"
    definition_period = YEAR


class SSP(Variable):
    value_type = float
    entity = Person
    label = u"Statutory Sick Pay"
    definition_period = YEAR


class employment_deductions(Variable):
    value_type = float
    entity = Person
    label = u"Deductions from employment income"
    definition_period = YEAR
    reference = "Income Tax Act (Earnings and Pensions) Act 2003 s. 327"

    def formula(person, period, parameters):
        DEDUCTIONS = ["employment_expenses"]
        return add(person, period, DEDUCTIONS)


class employment_expenses(Variable):
    value_type = float
    entity = Person
    label = (
        u"Cost of expenses necessarily incurred and reimbursed by employment"
    )
    definition_period = YEAR
    reference = "Income Tax Act (Earnings and Pensions) Act 2003 s. 333"


class pension_contributions(Variable):
    value_type = float
    entity = Person
    label = u"Amount contributed to registered pension schemes paid by the individual (not the employer)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return add(
            person,
            period,
            (
                "private_pension_contributions",
                "occupational_pension_contributions",
            ),
        )


class pension_contributions_relief(Variable):
    value_type = float
    entity = Person
    label = u"Reduction in taxable income from pension contributions"
    definition_period = YEAR
    reference = "Finance Act 2004 s. 188-194"

    def formula_2004_07_22(person, period, parameters):
        contributions = person("pension_contributions", period)
        pay = add(
            person, period, ["employment_income", "self_employment_income"]
        )
        under_75 = person("age", period) < 75
        basic_amount = parameters(
            period
        ).tax.income_tax.reliefs.pension_contribution.basic_amount
        tax_relief = min_(pay, max_(basic_amount, contributions)) * under_75
        capped_relief = min_(
            tax_relief, person("pension_annual_allowance", period)
        )
        return capped_relief


# Savings interest income


class taxable_savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = u"Amount of savings interest which is taxable"
    definition_period = YEAR
    reference = "Income Tax Act (Trading and Other Income) 2005 s. 369"

    def formula(person, period, parameters):
        total_interest = person("savings_interest_income", period)
        exempt_interest = person("tax_free_savings_income", period)
        return max_(0, total_interest - exempt_interest)


class tax_free_savings_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from savings in tax-free accounts"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("ISA_interest_income", period)


class ISA_interest_income(Variable):
    value_type = float
    entity = Person
    label = u"Amount received in interest from Individual Savings Accounts"
    definition_period = YEAR


# Trading income


class trading_loss(Variable):
    value_type = float
    entity = Person
    label = u"Loss from trading in the current year."
    definition_period = YEAR


class capital_allowances(Variable):
    value_type = float
    entity = Person
    label = u"Full relief from capital expenditure allowances"
    definition_period = YEAR
    reference = "Capital Allowances Act 2001 s. 1"


class loss_relief(Variable):
    value_type = float
    entity = Person
    label = u"Tax relief from trading losses"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 59"
    documentation = u"Can be set against general income."

    def formula(person, period, parameters):
        current_loss = person("trading_loss", period)
        previous_loss = person("trading_loss", period.last_year)
        return current_loss + previous_loss


# Pension income


class taxable_pension_income(Variable):
    value_type = float
    entity = Person
    label = u"Amount of pension income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 567"

    def formula(person, period, parameters):
        return person("pension_income", period)


# Social security income


class taxable_social_security_income(Variable):
    value_type = float
    entity = Person
    label = u"Amount of social security income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 658"

    def formula(person, period, parameters):
        return person("social_security_income", period)


# Trading income


class taxable_self_employment_income(Variable):
    value_type = float
    entity = Person
    label = u"Amount of trading income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 5"

    def formula(person, period, parameters):
        DEDUCTIONS = ["loss_relief", "capital_allowances", "trading_allowance"]
        return max_(
            0,
            person("self_employment_income", period)
            - add(person, period, DEDUCTIONS),
        )
        return amount


# Property income


class taxable_property_income(Variable):
    value_type = float
    entity = Person
    label = u"Amount of property income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 268"

    def formula(person, period, parameters):
        return max_(
            0,
            person("property_income", period)
            - person("property_allowance", period),
        )


# Dividend income


class deficiency_relief(Variable):
    value_type = float
    entity = Person
    label = u"Deficiency relief"
    definition_period = YEAR


class taxable_dividend_income(Variable):
    value_type = float
    entity = Person
    label = u"Amount of dividend income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 383"

    def formula(person, period, parameters):
        return max_(
            0,
            person("dividend_income", period)
            - person("deficiency_relief", period),
        )


# Miscellaneous income


class taxable_miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = u"Amount of miscellaneous income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 574"

    def formula(person, period, parameters):
        return person("miscellaneous_income", period)


class total_income(Variable):
    value_type = float
    entity = Person
    label = u"Taxable income after tax reliefs and before allowances"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 23"

    def formula(person, period, parameters):
        COMPONENTS = [
            "employment_income",
            "pension_income",
            "social_security_income",
            "self_employment_income",
            "property_income",
            "savings_interest_income",
            "dividend_income",
            "miscellaneous_income",
        ]
        return add(person, period, COMPONENTS)


class adjusted_net_income(Variable):
    value_type = float
    entity = Person
    label = u"Taxable income after tax reliefs and before allowances"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 23"

    def formula(person, period, parameters):
        COMPONENTS = [
            "taxable_employment_income",
            "taxable_pension_income",
            "taxable_social_security_income",
            "taxable_self_employment_income",
            "taxable_property_income",
            "taxable_savings_interest_income",
            "taxable_dividend_income",
            "taxable_miscellaneous_income",
        ]
        return max_(
            0,
            add(person, period, COMPONENTS),
        )

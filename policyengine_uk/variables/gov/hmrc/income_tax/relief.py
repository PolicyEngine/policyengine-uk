from policyengine_uk.model_api import *

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
    label = "Net taxable earnings"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 11"
    unit = GBP

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
    label = "Employment benefits"
    definition_period = YEAR
    unit = GBP

    adds = ["SSP", "SMP"]


class SMP(Variable):
    value_type = float
    entity = Person
    label = "Statutory Maternity Pay"
    definition_period = YEAR
    unit = GBP


class SSP(Variable):
    value_type = float
    entity = Person
    label = "Statutory Sick Pay"
    definition_period = YEAR
    unit = GBP


class employment_deductions(Variable):
    value_type = float
    entity = Person
    label = "Deductions from employment income"
    definition_period = YEAR
    reference = "Income Tax Act (Earnings and Pensions) Act 2003 s. 327"
    unit = GBP

    adds = ["employment_expenses"]


class employment_expenses(Variable):
    value_type = float
    entity = Person
    label = (
        "Cost of expenses necessarily incurred and reimbursed by employment"
    )
    definition_period = YEAR
    reference = "Income Tax Act (Earnings and Pensions) Act 2003 s. 333"
    unit = GBP


class pension_contributions(Variable):
    value_type = float
    entity = Person
    label = "Amount contributed to registered pension schemes paid by the individual (not the employer)"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        PENSIONS = [
            "private_pension_contributions",
            "occupational_pension_contributions",
        ]
        return add(person, period, PENSIONS)


class pension_contributions_relief(Variable):
    value_type = float
    entity = Person
    label = "Reduction in taxable income from pension contributions"
    definition_period = YEAR
    reference = "Finance Act 2004 s. 188-194"
    unit = GBP

    def formula_2004_07_22(person, period, parameters):
        contributions = person("pension_contributions", period)
        pay = add(
            person, period, ["employment_income", "self_employment_income"]
        )
        under_75 = person("age", period) < 75
        basic_amount = parameters(
            period
        ).gov.hmrc.income_tax.reliefs.pension_contribution.basic_amount
        tax_relief = min_(pay, contributions) * under_75
        return min_(
            tax_relief,
            max_(basic_amount, person("pension_annual_allowance", period)),
        )


# Savings interest income


class taxable_savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of savings interest which is taxable"
    definition_period = YEAR
    reference = "Income Tax Act (Trading and Other Income) 2005 s. 369"
    unit = GBP

    def formula(person, period, parameters):
        total_interest = person("savings_interest_income", period)
        exempt_interest = person("tax_free_savings_income", period)
        return max_(0, total_interest - exempt_interest)


class tax_free_savings_income(Variable):
    value_type = float
    entity = Person
    label = "Income from savings in tax-free accounts"
    definition_period = YEAR
    unit = GBP

    adds = ["ISA_interest_income"]


class ISA_interest_income(Variable):
    value_type = float
    entity = Person
    label = "Amount received in interest from Individual Savings Accounts"
    definition_period = YEAR
    unit = GBP


# Trading income


class trading_loss(Variable):
    value_type = float
    entity = Person
    label = "Loss from trading in the current year."
    definition_period = YEAR
    unit = GBP


class capital_allowances(Variable):
    value_type = float
    entity = Person
    label = "Full relief from capital expenditure allowances"
    definition_period = YEAR
    reference = "Capital Allowances Act 2001 s. 1"
    unit = GBP


class loss_relief(Variable):
    value_type = float
    entity = Person
    label = "Tax relief from trading losses"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 59"
    documentation = "Can be set against general income."
    unit = GBP

    def formula(person, period, parameters):
        current_loss = person("trading_loss", period)
        previous_loss = person("trading_loss", period.last_year)
        return current_loss + previous_loss


# Pension income


class taxable_pension_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of pension income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 567"
    unit = GBP

    adds = ["pension_income"]


# Social security income


class taxable_social_security_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of social security income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 658"
    unit = GBP

    adds = ["social_security_income"]


# Trading income


class taxable_self_employment_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of trading income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 5"
    unit = GBP

    def formula(person, period, parameters):
        self_employment_income = person("self_employment_income", period)
        DEDUCTIONS = ["loss_relief", "capital_allowances", "trading_allowance"]
        deductions = add(person, period, DEDUCTIONS)
        return max_(0, self_employment_income - deductions)


# Property income


class taxable_property_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of property income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 268"
    unit = GBP

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
    label = "Deficiency relief"
    definition_period = YEAR
    unit = GBP


class taxable_dividend_income(Variable):
    value_type = float
    entity = Person
    label = "Amount of dividend income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 383"
    unit = GBP

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
    label = "Amount of miscellaneous income that is taxable"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 574"
    unit = GBP

    adds = ["miscellaneous_income"]


class total_income(Variable):
    value_type = float
    entity = Person
    label = "Taxable income after tax reliefs and before allowances"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 23"
    unit = GBP

    adds = [
        "employment_income",
        "pension_income",
        "social_security_income",
        "self_employment_income",
        "property_income",
        "savings_interest_income",
        "dividend_income",
        "miscellaneous_income",
    ]


class adjusted_net_income(Variable):
    value_type = float
    entity = Person
    label = "Taxable income after tax reliefs and before allowances"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 23"
    unit = GBP

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
        if parameters(
            period
        ).gov.contrib.ubi_center.basic_income.interactions.include_in_taxable_income:
            COMPONENTS.append("basic_income")
        return max_(0, add(person, period, COMPONENTS))

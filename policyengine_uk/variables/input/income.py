from policyengine_uk.model_api import *

label = "Income"
description = "Financial income received by individuals."


class employment_income(Variable):
    value_type = float
    entity = Person
    label = "employment income"
    documentation = "Total income from employment. Include wages, bonuses, tips, etc."
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(a)"
    quantity_type = FLOW
    category = INCOME


class pension_income(Variable):
    value_type = float
    entity = Person
    label = "pension income"
    documentation = "Income from private or occupational pensions (not including the State Pension)"
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"
    quantity_type = FLOW


class state_pension(Variable):
    value_type = float
    entity = Person
    label = "State Pension"
    definition_period = YEAR
    unit = GBP
    documentation = "Gross State Pension payments"
    quantity_type = FLOW


class self_employment_income(Variable):
    value_type = float
    entity = Person
    label = "self-employment income"
    documentation = "Income from self-employment profits"
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(a)"
    quantity_type = FLOW


class property_income(Variable):
    value_type = float
    entity = Person
    label = "rental income"
    documentation = "Income from rental of property"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(b)"
    unit = GBP
    quantity_type = FLOW


class savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = "savings interest income"
    documentation = "Income from interest on savings, gross of tax"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(a)"
    unit = GBP
    quantity_type = FLOW


class dividend_income(Variable):
    value_type = float
    entity = Person
    label = "dividend income"
    documentation = "Total income from dividends, gross of tax"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(b-d)"
    unit = GBP
    quantity_type = FLOW


class sublet_income(Variable):
    value_type = float
    entity = Person
    label = "sublet income"
    documentation = "Income from subletting properties"
    definition_period = YEAR
    unit = GBP


class miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = "miscellaneous income"
    documentation = "Income from any other source"
    definition_period = YEAR
    unit = GBP


class private_transfer_income(Variable):
    value_type = float
    entity = Person
    label = "private transfer income"
    documentation = "Income from private transfers"
    definition_period = YEAR
    unit = GBP


class lump_sum_income(Variable):
    value_type = float
    entity = Person
    label = "lump sum income"
    documentation = "Income from lump sums"
    definition_period = YEAR
    unit = GBP


class maintenance_income(Variable):
    value_type = float
    entity = Person
    label = "maintenance payment income"
    documentation = "Income from maintenance payments to you"
    definition_period = YEAR
    unit = GBP


from policyengine_uk.model_api import *

label = "Income"
description = "Financial income received by individuals."


class employment_income(Variable):
    value_type = float
    entity = Person
    label = "Employment income"
    documentation = "Total income from employment"
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(a)"
    quantity_type = FLOW
    category = INCOME


class pension_income(Variable):
    value_type = float
    entity = Person
    label = "Pension income"
    documentation = "Income from private or occupational pensions (not including State Pension)"
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"
    quantity_type = FLOW



class self_employment_income(Variable):
    value_type = float
    entity = Person
    label = "Self-employment income"
    documentation = "Income from self-employment profits"
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(a)"
    quantity_type = FLOW


class property_income(Variable):
    value_type = float
    entity = Person
    label = "Rental income"
    documentation = "Income from rental of property"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(b)"
    unit = GBP
    quantity_type = FLOW


class savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = "Savings interest income"
    documentation = "Income from interest on savings, gross of tax"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(a)"
    unit = GBP
    quantity_type = FLOW


class dividend_income(Variable):
    value_type = float
    entity = Person
    label = "Income from dividends"
    documentation = "Total income from dividends, gross of tax"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(b-d)"
    unit = GBP
    quantity_type = FLOW


class sublet_income(Variable):
    value_type = float
    entity = Person
    label = "Income received from sublet agreements"
    definition_period = YEAR
    unit = GBP


class miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = "Income from other sources"
    definition_period = YEAR
    unit = GBP


class private_transfer_income(Variable):
    value_type = float
    entity = Person
    label = "Private transfers"
    definition_period = YEAR
    unit = GBP


class lump_sum_income(Variable):
    value_type = float
    entity = Person
    label = "Lump sum income"
    definition_period = YEAR
    unit = GBP


class maintenance_income(Variable):
    value_type = float
    entity = Person
    label = "Maintenance payments"
    definition_period = YEAR
    unit = GBP


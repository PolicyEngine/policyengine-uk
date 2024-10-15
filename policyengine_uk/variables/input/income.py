from policyengine_uk.model_api import *

label = "Income"
description = "Financial income received by individuals."


class employment_income(Variable):
    value_type = float
    entity = Person
    label = "employment income"
    documentation = "Total income from employment. Include wages, bonuses, tips, etc. This should be gross of all private pension contributions."
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(a)"
    quantity_type = FLOW
    adds = [
        "employment_income_before_lsr",
        "employment_income_behavioral_response",
        "employer_ni_fixed_employer_cost_change",
    ]
    uprating = "gov.obr.average_earnings"


class employment_income_before_lsr(Variable):
    value_type = float
    entity = Person
    label = "employment income before labor supply responses"
    unit = GBP
    definition_period = YEAR
    uprating = "gov.obr.average_earnings"


class private_pension_income(Variable):
    value_type = float
    entity = Person
    label = "pension income"
    documentation = "Income from private or occupational pensions (not including the State Pension)"
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"
    quantity_type = FLOW
    uprating = "gov.obr.non_labour_income"


class pension_income(Variable):
    value_type = float
    entity = Person
    label = "pension income"
    documentation = "Income from private or occupational pensions (not including the State Pension)"
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax (Earnings and Pensions) Act 2003 s. 1(1)(b)"
    quantity_type = FLOW
    uprating = "gov.obr.non_labour_income"


class state_pension(Variable):
    value_type = float
    entity = Person
    label = "State Pension"
    definition_period = YEAR
    unit = GBP
    documentation = "Gross State Pension payments"
    quantity_type = FLOW
    uprating = "gov.obr.consumer_price_index"

    def formula(person, period, parameters):
        gov = parameters(period).gov
        if gov.contrib.abolish_state_pension:
            return 0
        relative_increase = gov.contrib.cec.state_pension_increase
        uprating = 1 + relative_increase
        sp = gov.dwp.state_pension
        gender = person("gender", period).decode_to_str()
        is_sp_age = person("is_SP_age", period)
        return add(
            person,
            period,
            [
                "basic_state_pension",
                "additional_state_pension",
                "new_state_pension",
            ],
        )


class self_employment_income(Variable):
    value_type = float
    entity = Person
    label = "self-employment income"
    documentation = "Income from self-employment profits. This should be net of self-employment expenses."
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(a)"
    quantity_type = FLOW
    uprating = "gov.obr.mixed_income"


class property_income(Variable):
    value_type = float
    entity = Person
    label = "rental income"
    documentation = "Income from rental of property"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 1(1)(b)"
    unit = GBP
    quantity_type = FLOW
    uprating = "gov.obr.non_labour_income"


class savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = "savings interest income"
    documentation = "Income from interest on savings, gross of tax"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(a)"
    unit = GBP
    quantity_type = FLOW
    uprating = "gov.obr.non_labour_income"


class dividend_income(Variable):
    value_type = float
    entity = Person
    label = "dividend income"
    documentation = "Total income from dividends, gross of tax"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(b-d)"
    unit = GBP
    quantity_type = FLOW
    uprating = "gov.obr.non_labour_income"


class sublet_income(Variable):
    value_type = float
    entity = Person
    label = "sublet income"
    documentation = "Income from subletting properties"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.non_labour_income"


class miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = "miscellaneous income"
    documentation = "Income from any other source"
    definition_period = YEAR
    unit = GBP
    uprating = "gov.obr.non_labour_income"


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


class other_investment_income(Variable):
    value_type = float
    entity = Person
    label = "other investment income"
    documentation = "Investment income from sources other than dividends, property, and net interest on UK bank accounts; may include National Savings interest products, securities interest, interest from trusts or settlements, etc."
    definition_period = YEAR
    unit = GBP

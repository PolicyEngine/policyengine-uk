from policyengine_uk.model_api import *

"""
This file calculates the allowances to which taxpayers are entitled. This follows step 3 of the Income Tax Act 2007 s. 23.
"""


class personal_allowance(Variable):
    value_type = float
    entity = Person
    label = "Personal Allowance for the year"
    unit = GBP
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        PA = parameters(
            period
        ).gov.hmrc.income_tax.allowances.personal_allowance
        ANI = person("adjusted_net_income", period)
        excess = max_(0, ANI - PA.maximum_ANI)
        reduction = excess * PA.reduction_rate
        return max_(0, PA.amount - reduction)


class blind_persons_allowance(Variable):
    value_type = float
    entity = Person
    label = "Blind Person's Allowance for the year (not simulated)"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 38"
    unit = GBP


class married_couples_allowance(Variable):
    value_type = float
    entity = Person
    label = "Married Couples' allowance for the year"
    definition_period = YEAR
    unit = GBP


class married_couples_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = "Deduction from Married Couples' allowance for the year"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        rate = parameters(
            period
        ).gov.hmrc.income_tax.allowances.married_couples_allowance.deduction_rate
        return person("married_couples_allowance", period) * rate


class capped_mcad(Variable):
    label = "capped Married Couples' Allowance deduction"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        capping_value = add(
            person, period, ["income_tax_pre_charges", "CB_HITC"]
        )
        return min_(
            person("married_couples_allowance_deduction", period),
            capping_value,
        )


class pension_annual_allowance(Variable):
    value_type = float
    entity = Person
    label = "Annual Allowance for pension contributions"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        allowance = parameters(
            period
        ).gov.hmrc.income_tax.allowances.annual_allowance
        ANI = person("adjusted_net_income", period)
        reduction = max_(0, ANI - allowance.taper) * allowance.reduction_rate
        return max_(allowance.minimum, allowance.default - reduction)


class trading_allowance(Variable):
    value_type = float
    entity = Person
    label = "Trading Allowance for the year"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783AF"
    unit = GBP

    def formula(person, period, parameters):
        return parameters(
            period
        ).gov.hmrc.income_tax.allowances.trading_allowance


class trading_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = "Deduction applied by the trading allowance"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783AF"
    unit = GBP

    def formula(person, period, parameters):
        return min_(
            person("trading_allowance", period),
            person("self_employment_income", period),
        )


class property_allowance(Variable):
    value_type = float
    entity = Person
    label = "Property Allowance for the year"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783BF"
    unit = GBP

    def formula(person, period, parameters):
        return parameters(
            period
        ).gov.hmrc.income_tax.allowances.property_allowance


class property_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = "Deduction applied by the property allowance"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783AF"
    unit = GBP

    def formula(person, period, parameters):
        return min_(
            person("property_income", period),
            person("property_allowance", period),
        )


class savings_allowance(Variable):
    value_type = float
    entity = Person
    label = "Savings Allowance for the year"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 12B"
    unit = GBP

    def formula(person, period, parameters):
        tax_band = person("tax_band", period)
        tax_bands = tax_band.possible_values
        amounts = parameters(
            period
        ).gov.hmrc.income_tax.allowances.personal_savings_allowance
        return select(
            [
                tax_band == tax_bands.ADDITIONAL,
                tax_band == tax_bands.HIGHER,
                (
                    (tax_band == tax_bands.STARTER)
                    | (tax_band == tax_bands.BASIC)
                    | (tax_band == tax_bands.INTERMEDIATE)
                ),
                tax_band == tax_bands.NONE,
            ],
            [amounts.additional, amounts.higher, amounts.basic, amounts.basic],
        )


class dividend_allowance(Variable):
    value_type = float
    entity = Person
    label = "Dividend allowance for the person"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 13A"
    unit = GBP

    def formula(person, period, parameters):
        return parameters(
            period
        ).gov.hmrc.income_tax.allowances.dividend_allowance


class gift_aid(Variable):
    value_type = float
    entity = Person
    label = "Expenditure under Gift Aid"
    definition_period = YEAR
    unit = GBP


class covenanted_payments(Variable):
    value_type = float
    entity = Person
    label = "Covenanted payments to charities"
    definition_period = YEAR
    unit = GBP


class charitable_investment_gifts(Variable):
    value_type = float
    entity = Person
    label = "Gifts of qualifying investment or property to charities"
    definition_period = YEAR
    unit = GBP


class other_deductions(Variable):
    value_type = float
    entity = Person
    label = "All other tax deductions"
    definition_period = YEAR
    unit = GBP


class allowances(Variable):
    value_type = float
    entity = Person
    label = "Allowances applicable to adjusted net income"
    definition_period = YEAR
    unit = GBP

    adds = [
        "personal_allowance",
        "blind_persons_allowance",
        "gift_aid",
        "covenanted_payments",
        "charitable_investment_gifts",
        "other_deductions",
    ]

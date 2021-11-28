from openfisca_uk.tools.general import *
from openfisca_uk.entities import *
from openfisca_uk.variables.finance.tax.income_tax.liability import TaxBand

"""
This file calculates the allowances to which taxpayers are entitled. This follows step 3 of the Income Tax Act 2007 s. 23.
"""


class personal_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Personal Allowance for the year"
    unit = "currency-GBP"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 35"

    def formula(person, period, parameters):
        PA = parameters(period).tax.income_tax.allowances.personal_allowance
        ANI = person("adjusted_net_income", period)
        excess = max_(0, ANI - PA.maximum_ANI)
        reduction = excess * PA.reduction_rate
        amount = max_(0, PA.amount - reduction)
        return amount


class blind_persons_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Blind Person's Allowance for the year (not simulated)"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 38"


class unused_personal_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Unused personal allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return max_(
            person("personal_allowance", period)
            - person("adjusted_net_income", period),
            0,
        )


class marriage_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Marriage Allowance for the year (a tax-reducer, rather than an allowance or tax relief)"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 55"

    def formula(person, period, parameters):
        tax_band = person("tax_band", period)
        bands = tax_band.possible_values
        under_PA = person("tax_band", period) == bands.NONE
        band = person("tax_band", period)
        # Marriage Allowance is eligible for couples with one in the basic rate bracket and
        # one not in a tax bracket. For those paying Scottish rates, the taxpayer can be in
        # the starter or intermediate rate brackets.
        meets_band_eligibility = np.isin(
            band, (bands.STARTER, bands.BASIC, bands.INTERMEDIATE)
        )
        marital = person("marital_status", period)
        married = marital == marital.possible_values.MARRIED
        transferable_allowance = person.benunit.sum(
            married
            * under_PA
            * min_(
                person("unused_personal_allowance", period),
                0.1 * person("personal_allowance", period),
            )
        )
        return married * meets_band_eligibility * transferable_allowance


class married_couples_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Married Couples' allowance for the year"
    definition_period = YEAR


class married_couples_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = u"Deduction from Married Couples' allowance for the year"
    definition_period = YEAR

    def formula(person, period, parameters):
        rate = parameters(
            period
        ).tax.income_tax.allowances.married_couples_allowance.deduction_rate
        return person("married_couples_allowance", period) * rate


class pension_annual_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Annual Allowance for pension contributions"
    definition_period = YEAR

    def formula(person, period, parameters):
        allowance = parameters(
            period
        ).tax.income_tax.allowances.annual_allowance
        ANI = person("adjusted_net_income", period)
        reduction = max_(0, ANI - allowance.taper) * allowance.reduction_rate
        amount = max_(allowance.minimum, allowance.default - reduction)
        return amount


class trading_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Trading Allowance for the year"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783AF"

    def formula(person, period, parameters):
        return parameters(period).tax.income_tax.allowances.trading_allowance


class trading_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = u"Deduction applied by the trading allowance"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783AF"

    def formula(person, period, parameters):
        amount = min_(
            person("trading_allowance", period),
            person("self_employment_income", period),
        )
        return amount


class property_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Property Allowance for the year"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783BF"

    def formula(person, period, parameters):
        return parameters(period).tax.income_tax.allowances.property_allowance


class property_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = u"Deduction applied by the property allowance"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 783AF"

    def formula(person, period, parameters):
        amount = min_(
            person("property_income", period),
            person("property_allowance", period),
        )
        return amount


class savings_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Savings Allowance for the year"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 12B"

    def formula(person, period, parameters):
        tax_band = person("tax_band", period)
        tax_bands = tax_band.possible_values
        amounts = parameters(
            period
        ).tax.income_tax.allowances.personal_savings_allowance
        allowance = select(
            [
                tax_band == tax_bands.ADDITIONAL,
                tax_band == tax_bands.HIGHER,
                tax_band == tax_bands.BASIC,
                tax_band == tax_bands.NONE,
            ],
            [amounts.additional, amounts.higher, amounts.basic, amounts.basic],
        )
        return allowance


class dividend_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Dividend allowance for the person"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 13A"

    def formula(person, period, parameters):
        amount = parameters(
            period
        ).tax.income_tax.allowances.dividend_allowance
        return amount


class gift_aid(Variable):
    value_type = float
    entity = Person
    label = u"Expenditure under Gift Aid"
    definition_period = YEAR


class covenanted_payments(Variable):
    value_type = float
    entity = Person
    label = u"Covenanted payments to charities"
    definition_period = YEAR


class charitable_investment_gifts(Variable):
    value_type = float
    entity = Person
    label = u"Gifts of qualifying investment or property to charities"
    definition_period = YEAR


class other_deductions(Variable):
    value_type = float
    entity = Person
    label = u"All other tax deductions"
    definition_period = YEAR


class allowances(Variable):
    value_type = float
    entity = Person
    label = u"Allowances applicable to adjusted net income"
    definition_period = YEAR

    def formula(person, period, parameters):
        ALLOWANCES = [
            "personal_allowance",
            "blind_persons_allowance",
            "gift_aid",
            "covenanted_payments",
            "charitable_investment_gifts",
            "other_deductions",
        ]
        allowance = add(person, period, ALLOWANCES)
        return allowance

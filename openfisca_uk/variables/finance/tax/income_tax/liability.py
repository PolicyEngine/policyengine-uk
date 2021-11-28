from openfisca_uk.tools.general import *
from openfisca_uk.entities import *

"""
This file calculates the overall liability for Income Tax.
"""


class earned_taxable_income(Variable):
    value_type = float
    entity = Person
    label = u"Non-savings, non-dividend income for Income Tax"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 10"

    def formula(person, period, parameters):
        amount = person("adjusted_net_income", period) - add(
            person,
            period,
            ["taxable_savings_interest_income", "taxable_dividend_income"],
        )
        reductions = add(person, period, ["allowances", "marriage_allowance"])
        final_amount = max_(0, amount - reductions)
        return final_amount


class taxed_income(Variable):
    value_type = float
    entity = Person
    label = u"Income which is taxed"
    definition_period = YEAR

    def formula(person, period, parameters):
        COMPONENTS = [
            "earned_taxable_income",
            "taxed_savings_income",
            "taxed_dividend_income",
        ]
        return add(person, period, COMPONENTS)


class basic_rate_earned_income(Variable):
    value_type = float
    entity = Person
    label = u"Earned income (non-savings, non-dividend) at the basic rate"
    definition_period = YEAR

    def formula(person, period, parameters):
        income = person("earned_taxable_income", period)
        rates = parameters(period).tax.income_tax.rates
        amount = clip(income, rates.uk.thresholds[0], rates.uk.thresholds[1])
        return amount


class higher_rate_earned_income(Variable):
    value_type = float
    entity = Person
    label = u"Earned income (non-savings, non-dividend) at the higher rate"
    definition_period = YEAR

    def formula(person, period, parameters):
        income = person("earned_taxable_income", period)
        rates = parameters(period).tax.income_tax.rates
        amount = (
            clip(income, rates.uk.thresholds[1], rates.uk.thresholds[2])
            - rates.uk.thresholds[1]
        )
        return amount


class add_rate_earned_income(Variable):
    value_type = float
    entity = Person
    label = u"Earned income (non-savings, non-dividend) at the additional rate"
    definition_period = YEAR

    def formula(person, period, parameters):
        income = person("earned_taxable_income", period)
        rates = parameters(period).tax.income_tax.rates
        amount = (
            clip(income, rates.uk.thresholds[2], inf) - rates.uk.thresholds[2]
        )
        return amount


class basic_rate_earned_income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Income tax on earned income at the basic rate"
    definition_period = YEAR

    def formula(person, period, parameters):
        amount = person("basic_rate_earned_income", period)
        charge = parameters(period).tax.income_tax.rates.uk.rates[0] * amount
        return charge


class higher_rate_earned_income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Income tax on earned income at the higher rate"
    definition_period = YEAR

    def formula(person, period, parameters):
        amount = person("higher_rate_earned_income", period)
        charge = parameters(period).tax.income_tax.rates.uk.rates[1] * amount
        return charge


class add_rate_earned_income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Income tax on earned income at the additional rate"
    definition_period = YEAR

    def formula(person, period, parameters):
        amount = person("add_rate_earned_income", period)
        charge = parameters(period).tax.income_tax.rates.uk.rates[2] * amount
        return charge


class earned_income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Income tax on earned income"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 10"

    def formula(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates
        uk_amount = rates.uk.calc(person("earned_taxable_income", period))
        return uk_amount

    def formula_2017_04_06(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        uk_amount = rates.uk.calc(person("earned_taxable_income", period))
        scot_amount = rates.scotland.pre_starter_rate.calc(
            person("earned_taxable_income", period)
        )
        amount = where(scot, scot_amount, uk_amount)
        return amount

    def formula_2018_04_06(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        uk_amount = rates.uk.calc(person("earned_taxable_income", period))
        scot_amount = rates.scotland.post_starter_rate.calc(
            person("earned_taxable_income", period)
        )
        amount = where(scot, scot_amount, uk_amount)
        return amount


class TaxBand(Enum):
    NONE = "None"
    STARTER = "Starter (Scottish rates)"
    BASIC = "Basic"
    INTERMEDIATE = "Intermediate (Scottish rates)"
    HIGHER = "Higher"
    ADDITIONAL = "Additional"


class pays_scottish_income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Whether the individual pays Scottish Income Tax rates"
    definition_period = YEAR

    def formula(person, period, parameters):
        country = person.household("country", period)
        countries = country.possible_values
        return person.household("country", period) == countries.SCOTLAND


class tax_band(Variable):
    value_type = Enum
    possible_values = TaxBand
    default_value = TaxBand.NONE
    entity = Person
    label = u"Tax band of the individual"
    definition_period = YEAR

    def formula(person, period, parameters):
        allowances = person("allowances", period)
        ANI = person("adjusted_net_income", period)
        rates = parameters(period).tax.income_tax.rates
        basic = allowances + rates.uk.thresholds[0]
        higher = allowances + rates.uk.thresholds[-2]
        add = allowances + rates.uk.thresholds[-1]
        band = select(
            [ANI >= add, ANI >= higher, ANI > basic, ANI <= basic],
            [TaxBand.ADDITIONAL, TaxBand.HIGHER, TaxBand.BASIC, TaxBand.NONE],
        )
        return band

    def formula_2017_04_06(person, period, parameters):
        allowances = person("allowances", period)
        ANI = person("adjusted_net_income", period)
        rates = parameters(period).tax.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        income = ANI - allowances
        uk_band = select(
            [income < threshold for threshold in rates.uk.thresholds] + [True],
            [TaxBand.NONE, TaxBand.BASIC, TaxBand.HIGHER, TaxBand.ADDITIONAL],
        )
        scottish_band = select(
            [
                income < threshold
                for threshold in rates.scotland.pre_starter_rate.thresholds
            ]
            + [True],
            [TaxBand.NONE, TaxBand.BASIC, TaxBand.HIGHER, TaxBand.ADDITIONAL],
        )
        return where(scot, scottish_band, uk_band)

    def formula_2018_06_01(person, period, parameters):
        allowances = person("allowances", period)
        ANI = person("adjusted_net_income", period)
        rates = parameters(period).tax.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        income = ANI - allowances
        uk_band = select(
            [income < threshold for threshold in rates.uk.thresholds[:3]]
            + [True],
            [TaxBand.NONE, TaxBand.BASIC, TaxBand.HIGHER, TaxBand.ADDITIONAL],
        )
        scottish_band = select(
            [
                income < threshold
                for threshold in rates.scotland.post_starter_rate.thresholds[
                    :5
                ]
            ]
            + [True],
            [
                TaxBand.NONE,
                TaxBand.STARTER,
                TaxBand.BASIC,
                TaxBand.INTERMEDIATE,
                TaxBand.HIGHER,
                TaxBand.ADDITIONAL,
            ],
        )
        return where(scot, scottish_band, uk_band)


class basic_rate_savings_income_pre_starter(Variable):
    value_type = float
    entity = Person
    label = u"Savings income which would otherwise be taxed at the basic rate, without the starter rate"
    definition_period = YEAR

    def formula(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates.uk
        savings_income_total = person(
            "taxable_savings_interest_income", period
        )
        savings_allowance = person("savings_allowance", period)
        savings_income = max_(0, savings_income_total - savings_allowance)
        other_income = person("earned_taxable_income", period)
        basic_rate_amount_with_savings = clip(
            savings_income + other_income,
            rates.thresholds[0],
            rates.thresholds[1],
        )
        basic_rate_amount_without_savings = clip(
            other_income, rates.thresholds[0], rates.thresholds[1]
        )
        amount = (
            basic_rate_amount_with_savings - basic_rate_amount_without_savings
        )
        return amount


class savings_starter_rate_income(Variable):
    value_type = float
    entity = Person
    label = u"Savings income which is tax-free under the starter rate"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 12"

    def formula(person, period, parameters):
        income = person("basic_rate_savings_income_pre_starter", period)
        limit = parameters(
            period
        ).tax.income_tax.rates.savings_starter_rate.allowance
        return max_(0, limit - income)


class basic_rate_savings_income(Variable):
    value_type = float
    entity = Person
    label = u"Savings income at the basic rate"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"

    def formula(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates
        other_income = person("earned_taxable_income", period)
        savings_deductions = add(
            person,
            period,
            ["savings_allowance", "savings_starter_rate_income"],
        )
        savings_income_less_deductions = max_(
            0,
            person("taxable_savings_interest_income", period)
            - savings_deductions,
        )
        basic_rate_amount_with = clip(
            other_income + savings_income_less_deductions,
            rates.uk.thresholds[0],
            rates.uk.thresholds[1],
        )
        basic_rate_amount_without = clip(
            other_income, rates.uk.thresholds[0], rates.uk.thresholds[1]
        )
        basic_rate_amount = max_(
            0, basic_rate_amount_with - basic_rate_amount_without
        )
        return basic_rate_amount


class higher_rate_savings_income(Variable):
    value_type = float
    entity = Person
    label = u"Savings income at the higher rate"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"

    def formula(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates
        other_income = person("earned_taxable_income", period)
        savings_deductions = add(
            person,
            period,
            ["savings_allowance", "savings_starter_rate_income"],
        )
        savings_income_less_deductions = max_(
            0,
            person("taxable_savings_interest_income", period)
            - savings_deductions,
        )
        higher_rate_amount_with = clip(
            other_income + savings_income_less_deductions,
            rates.uk.thresholds[1],
            rates.uk.thresholds[2],
        )
        higher_rate_amount_without = clip(
            other_income, rates.uk.thresholds[1], rates.uk.thresholds[2]
        )
        higher_rate_amount = max_(
            0, higher_rate_amount_with - higher_rate_amount_without
        )
        return higher_rate_amount


class add_rate_savings_income(Variable):
    value_type = float
    entity = Person
    label = u"Savings income at the higher rate"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"

    def formula(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates
        other_income = person("earned_taxable_income", period)
        savings_deductions = add(
            person,
            period,
            ["savings_allowance", "savings_starter_rate_income"],
        )
        savings_income_less_deductions = max_(
            0,
            person("taxable_savings_interest_income", period)
            - savings_deductions,
        )
        add_rate_amount_with = clip(
            other_income + savings_income_less_deductions,
            rates.uk.thresholds[2],
            inf,
        )
        add_rate_amount_without = clip(
            other_income, rates.uk.thresholds[2], inf
        )
        add_rate_amount = max_(
            0, add_rate_amount_with - add_rate_amount_without
        )
        return add_rate_amount


class taxed_savings_income(Variable):
    value_type = float
    entity = Person
    label = u"Savings income which advances the person's income tax schedule"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"

    def formula(person, period, parameters):
        COMPONENTS = [
            "basic_rate_savings_income",
            "higher_rate_savings_income",
            "add_rate_savings_income",
        ]
        amount = add(person, period, COMPONENTS)
        return amount


class taxed_dividend_income(Variable):
    value_type = float
    entity = Person
    label = u"Dividend income which is taxed"
    definition_period = YEAR

    def formula(person, period, parameters):
        return max_(
            0,
            person("taxable_dividend_income", period)
            - person("dividend_allowance", period),
        )


class savings_income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Income tax on savings income"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"

    def formula(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates
        basic_rate_amount = person("basic_rate_savings_income", period)
        higher_rate_amount = person("higher_rate_savings_income", period)
        add_rate_amount = person("add_rate_savings_income", period)
        charge = (
            rates.uk.rates[0] * basic_rate_amount
            + rates.uk.rates[1] * higher_rate_amount
            + rates.uk.rates[2] * add_rate_amount
        )
        return charge


class dividend_income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Income tax on dividend income"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 13"

    def formula(person, period, parameters):
        rates = parameters(period).tax.income_tax.rates
        other_income = person("earned_taxable_income", period) + person(
            "taxed_savings_income", period
        )
        taxable_dividends = person("taxed_dividend_income", period)
        tax_with_dividends = rates.dividends.calc(
            other_income + taxable_dividends
        )
        tax_without_dividends = rates.dividends.calc(other_income)
        dividend_tax = tax_with_dividends - tax_without_dividends
        return dividend_tax


class income_tax_pre_charges(Variable):
    value_type = float
    entity = Person
    label = u"Income Tax before any tax charges"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 23"

    def formula(person, period, parameters):
        COMPONENTS = [
            "earned_income_tax",
            "savings_income_tax",
            "dividend_income_tax",
        ]
        total = add(person, period, COMPONENTS)
        return total


class is_higher_earner(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person is the highest earner in a family"
    definition_period = YEAR

    def formula(person, period, parameters):
        income = person("adjusted_net_income", period)
        # Add noise to incomes in order to avoid ties
        return (
            person.get_rank(person.benunit, -income + random(person) * 1e-2)
            == 0
        )


class CB_HITC(Variable):
    value_type = float
    entity = Person
    label = u"Child Benefit High-Income Tax Charge"
    definition_period = YEAR
    reference = "Finance Act 2012 s. 681B"

    def formula(person, period, parameters):
        CB_received = person.benunit("child_benefit", period, options=[ADD])
        CB_HITC = parameters(period).tax.income_tax.charges.CB_HITC
        phase_length = CB_HITC.phase_out_end - CB_HITC.phase_out_start
        income = amount_between(
            person("adjusted_net_income", period),
            CB_HITC.phase_out_start,
            CB_HITC.phase_out_end,
        )
        percentage = income / phase_length
        return (percentage * CB_received) * person("is_higher_earner", period)


class income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income Tax"
    documentation = "Total Income Tax liability"
    definition_period = YEAR
    unit = "currency-GBP"
    reference = "Income Tax Act 2007 s. 23"

    def formula(person, period, parameters):
        return max_(
            0,
            add(person, period, ["income_tax_pre_charges", "CB_HITC"])
            - person("married_couples_allowance_deduction", period),
        )

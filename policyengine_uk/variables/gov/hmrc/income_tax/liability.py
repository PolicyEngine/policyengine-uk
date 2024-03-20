from policyengine_uk.model_api import *

"""
This file calculates the overall liability for Income Tax.
"""


class earned_taxable_income(Variable):
    value_type = float
    entity = Person
    label = "Non-savings, non-dividend income for Income Tax"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 10"
    unit = GBP

    def formula(person, period, parameters):
        EXCLUSIONS = [
            "taxable_savings_interest_income",
            "taxable_dividend_income",
            "allowances",
            "marriage_allowance",
            "pension_contributions_relief",
        ]
        ANI = person("adjusted_net_income", period)
        exclusions = add(person, period, EXCLUSIONS)
        return max_(0, ANI - exclusions)


class taxed_income(Variable):
    value_type = float
    entity = Person
    label = "Income which is taxed"
    definition_period = YEAR
    unit = GBP

    adds = [
        "earned_taxable_income",
        "taxed_savings_income",
        "taxed_dividend_income",
    ]


class basic_rate_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Earned income (non-savings, non-dividend) at the basic rate"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        income = person("earned_taxable_income", period)
        thresholds = parameters(period).gov.hmrc.income_tax.rates.uk.thresholds
        return clip(income, thresholds[0], thresholds[1])


class higher_rate_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Earned income (non-savings, non-dividend) at the higher rate"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        income = person("earned_taxable_income", period)
        thresholds = parameters(period).gov.hmrc.income_tax.rates.uk.thresholds
        return clip(income, thresholds[1], thresholds[2]) - thresholds[1]


class add_rate_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Earned income (non-savings, non-dividend) at the additional rate"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        income = person("earned_taxable_income", period)
        thresholds = parameters(period).gov.hmrc.income_tax.rates.uk.thresholds
        return clip(income, thresholds[2], inf) - thresholds[2]


class basic_rate_earned_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax on earned income at the basic rate"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        amount = person("basic_rate_earned_income", period)
        return (
            parameters(period).gov.hmrc.income_tax.rates.uk.rates[0] * amount
        )


class higher_rate_earned_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax on earned income at the higher rate"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        amount = person("higher_rate_earned_income", period)
        return (
            parameters(period).gov.hmrc.income_tax.rates.uk.rates[1] * amount
        )


class add_rate_earned_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax on earned income at the additional rate"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        amount = person("add_rate_earned_income", period)
        return (
            parameters(period).gov.hmrc.income_tax.rates.uk.rates[2] * amount
        )


class earned_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax on earned income"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 10"
    unit = GBP

    def formula(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates
        return rates.uk.calc(person("earned_taxable_income", period))

    def formula_2017_04_06(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        uk_amount = rates.uk.calc(person("earned_taxable_income", period))
        scot_amount = rates.scotland.pre_starter_rate.calc(
            person("earned_taxable_income", period)
        )
        return where(scot, scot_amount, uk_amount)

    def formula_2018_04_06(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        uk_amount = rates.uk.calc(person("earned_taxable_income", period))
        scot_amount = rates.scotland.post_starter_rate.calc(
            person("earned_taxable_income", period)
        )
        return where(scot, scot_amount, uk_amount)


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
    label = "Whether the individual pays Scottish Income Tax rates"
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
    label = "Tax band of the individual"
    definition_period = YEAR

    def formula(person, period, parameters):
        allowances = person("allowances", period)
        ANI = person("adjusted_net_income", period)
        rates = parameters(period).gov.hmrc.income_tax.rates
        basic = allowances + rates.uk.thresholds[0]
        higher = allowances + rates.uk.thresholds[-2]
        add = allowances + rates.uk.thresholds[-1]
        return select(
            [ANI >= add, ANI >= higher, ANI > basic],
            [TaxBand.ADDITIONAL, TaxBand.HIGHER, TaxBand.BASIC],
            default=TaxBand.NONE,
        )

    def formula_2017_04_06(person, period, parameters):
        allowances = person("allowances", period)
        ANI = person("adjusted_net_income", period)
        rates = parameters(period).gov.hmrc.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        income = ANI - allowances
        uk_band = select(
            [income < threshold for threshold in rates.uk.thresholds[:3]],
            [TaxBand.NONE, TaxBand.BASIC, TaxBand.HIGHER],
            default=TaxBand.ADDITIONAL,
        )
        scottish_band = select(
            [
                income < threshold
                for threshold in rates.scotland.pre_starter_rate.thresholds[:3]
            ],
            [TaxBand.NONE, TaxBand.BASIC, TaxBand.HIGHER],
            default=TaxBand.ADDITIONAL,
        )
        return where(scot, scottish_band, uk_band)

    def formula_2018_06_01(person, period, parameters):
        allowances = person("allowances", period)
        ANI = person("adjusted_net_income", period)
        rates = parameters(period).gov.hmrc.income_tax.rates
        scot = person("pays_scottish_income_tax", period)
        income = ANI - allowances
        uk_band = select(
            [income < threshold for threshold in rates.uk.thresholds[:3]],
            [TaxBand.NONE, TaxBand.BASIC, TaxBand.HIGHER],
            default=TaxBand.ADDITIONAL,
        )
        scottish_band = select(
            [
                income < threshold
                for threshold in rates.scotland.post_starter_rate.thresholds[
                    :5
                ]
            ],
            [
                TaxBand.NONE,
                TaxBand.STARTER,
                TaxBand.BASIC,
                TaxBand.INTERMEDIATE,
                TaxBand.HIGHER,
            ],
            default=TaxBand.ADDITIONAL,
        )
        return where(scot, scottish_band, uk_band)


class basic_rate_savings_income_pre_starter(Variable):
    value_type = float
    entity = Person
    label = "Savings income which would otherwise be taxed at the basic rate, without the starter rate"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        thresholds = parameters(period).gov.hmrc.income_tax.rates.uk.thresholds
        savings_income_total = person(
            "taxable_savings_interest_income", period
        )
        savings_allowance = person("savings_allowance", period)
        savings_income = max_(0, savings_income_total - savings_allowance)
        other_income = person("earned_taxable_income", period)
        basic_rate_amount_with_savings = clip(
            savings_income + other_income,
            thresholds[0],
            thresholds[1],
        )
        basic_rate_amount_without_savings = clip(
            other_income, thresholds[0], thresholds[1]
        )
        return (
            basic_rate_amount_with_savings - basic_rate_amount_without_savings
        )


class savings_starter_rate_income(Variable):
    value_type = float
    entity = Person
    label = "Savings income which is tax-free under the starter rate"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 12"
    unit = GBP

    def formula(person, period, parameters):
        income = person("basic_rate_savings_income_pre_starter", period)
        limit = parameters(
            period
        ).gov.hmrc.income_tax.rates.savings_starter_rate.allowance
        return max_(0, limit - income)


class basic_rate_savings_income(Variable):
    value_type = float
    entity = Person
    label = "Savings income at the basic rate"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"
    unit = GBP

    def formula(person, period, parameters):
        thresholds = parameters(period).gov.hmrc.income_tax.rates.uk.thresholds
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
            thresholds[0],
            thresholds[1],
        )
        basic_rate_amount_without = clip(
            other_income, thresholds[0], thresholds[1]
        )
        return max_(0, basic_rate_amount_with - basic_rate_amount_without)


class higher_rate_savings_income(Variable):
    value_type = float
    entity = Person
    label = "Savings income at the higher rate"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"
    unit = GBP

    def formula(person, period, parameters):
        thresholds = parameters(period).gov.hmrc.income_tax.rates.uk.thresholds
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
            thresholds[1],
            thresholds[2],
        )
        higher_rate_amount_without = clip(
            other_income, thresholds[1], thresholds[2]
        )
        return max_(0, higher_rate_amount_with - higher_rate_amount_without)


class add_rate_savings_income(Variable):
    value_type = float
    entity = Person
    label = "Savings income at the higher rate"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"
    unit = GBP

    def formula(person, period, parameters):
        thresholds = parameters(period).gov.hmrc.income_tax.rates.uk.thresholds
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
            thresholds[2],
            inf,
        )
        add_rate_amount_without = clip(other_income, thresholds[2], inf)
        return max_(0, add_rate_amount_with - add_rate_amount_without)


class taxed_savings_income(Variable):
    value_type = float
    entity = Person
    label = "Savings income which advances the person's income tax schedule"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"
    unit = GBP

    adds = [
        "basic_rate_savings_income",
        "higher_rate_savings_income",
        "add_rate_savings_income",
    ]


class taxed_dividend_income(Variable):
    value_type = float
    entity = Person
    label = "Dividend income which is taxed"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        return max_(
            0,
            person("taxable_dividend_income", period)
            - person("dividend_allowance", period),
        )


class savings_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax on savings income"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 11D"
    unit = GBP

    def formula(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates.uk.rates
        basic_rate_amount = person("basic_rate_savings_income", period)
        higher_rate_amount = person("higher_rate_savings_income", period)
        add_rate_amount = person("add_rate_savings_income", period)
        return (
            rates[0] * basic_rate_amount
            + rates[1] * higher_rate_amount
            + rates[2] * add_rate_amount
        )


class dividend_income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income tax on dividend income"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 13"
    unit = GBP

    def formula(person, period, parameters):
        rates = parameters(period).gov.hmrc.income_tax.rates
        other_income = person("earned_taxable_income", period) + person(
            "taxed_savings_income", period
        )
        taxable_dividends = person("taxed_dividend_income", period)
        tax_with_dividends = rates.dividends.calc(
            other_income + taxable_dividends
        )
        tax_without_dividends = rates.dividends.calc(other_income)
        return tax_with_dividends - tax_without_dividends


class income_tax_pre_charges(Variable):
    value_type = float
    entity = Person
    label = "Income Tax before any tax charges"
    definition_period = YEAR
    reference = "Income Tax Act 2007 s. 23"
    unit = GBP

    adds = [
        "earned_income_tax",
        "savings_income_tax",
        "dividend_income_tax",
    ]


class is_higher_earner(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is the highest earner in a family"
    definition_period = YEAR

    def formula(person, period, parameters):
        income = person("adjusted_net_income", period)
        # Add noise to incomes in order to avoid ties
        return (
            person.get_rank(person.benunit, -income + random(person) * 1e-2)
            == 0
        )


class income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income Tax"
    documentation = "Total Income Tax liability"
    definition_period = YEAR
    unit = GBP
    reference = "Income Tax Act 2007 s. 23"
    category = TAX
    adds = [
        "earned_income_tax",
        "savings_income_tax",
        "dividend_income_tax",
        "CB_HITC",
    ]
    subtracts = [
        "capped_mcad",
    ]

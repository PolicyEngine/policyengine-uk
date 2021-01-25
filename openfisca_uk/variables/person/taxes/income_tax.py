from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class taxable_income(Variable):
    value_type = float
    entity = Person
    label = u"Taxable income, before deductions"
    definition_period = YEAR

    def formula(person, period, parameters):
        COMPONENTS = [
            "gross_wage",
            "gross_profit",
            "SSP",
            "SMP",
            "SPP",
            "holiday_pay",
            "state_pension",
            "pension_income",
            "rental_income",
            "BSP",
            "ESA_contrib",
            "JSA_contrib",
            "savings_interest",
        ]
        return max_(0, add(person, period, COMPONENTS, options=[MATCH]))


class personal_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Personal Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        PA = parameters(period).taxes.income_tax.allowances.personal_allowance
        applicable_income = person("taxable_income", period)
        allowance = max_(0, PA.amount - PA.reduction.calc(applicable_income))
        return allowance


class personal_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = u"Deduction from taxes using the Personal Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return min_(
            person("personal_allowance", period),
            person("taxable_income", period),
        )


class unused_personal_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Amount of unused personal allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return max_(
            0,
            person("personal_allowance", period)
            - person("taxable_income", period),
        )


class marriage_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Amount of Marriage Allowance entitled"
    definition_period = YEAR

    def formula(person, period, parameters):
        max_amount = parameters(
            period
        ).taxes.income_tax.allowances.marriage_allowance
        spousal_personal_allowance = person.benunit.sum(
            person.benunit.members("unused_personal_allowance", period)
        ) - person("unused_personal_allowance", period)
        return min_(
            max_amount,
            spousal_personal_allowance * person.benunit("is_married", period),
        )


class marriage_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = u"Deduction from the Marriage Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return min_(
            person("marriage_allowance", period),
            person("taxable_income", period),
        )


class personal_savings_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Allowance for savings interest"
    definition_period = YEAR

    def formula(person, period, parameters):
        income_tax = parameters(period).taxes.income_tax
        rates = income_tax.rates.uk
        PSA = income_tax.allowances.personal_savings_allowance
        applicable_amount = person("taxable_income", period)
        in_basic_threshold = (applicable_amount >= rates.thresholds[0]) * (
            applicable_amount < rates.thresholds[1]
        )
        in_higher_threshold = (applicable_amount >= rates.thresholds[1]) * (
            applicable_amount < rates.thresholds[2]
        )
        allowance = where(
            in_basic_threshold,
            PSA.basic,
            where(in_higher_threshold, PSA.higher, PSA.additional),
        )
        return allowance


class personal_savings_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = u"Deduction from the Personal Savings Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return min_(
            person("personal_savings_allowance", period),
            max_(0, person("savings_interest", period)),
        )


class savings_starter_allowance_deduction(Variable):
    value_type = float
    entity = Person
    label = u"Deduction from the Savings Starter Allowance"
    definition_period = YEAR

    def formula(person, period, parameters):
        return min_(
            person("savings_starter_allowance", period),
            max_(0, person("savings_interest", period)),
        )


class savings_starter_allowance(Variable):
    value_type = float
    entity = Person
    label = u"Starter rate for savings"
    definition_period = YEAR

    def formula(person, period, parameters):
        starter_rate = parameters(
            period
        ).taxes.income_tax.allowances.savings_starter_rate
        applicable_amount = person("taxable_income", period)
        PA = person("personal_allowance", period)
        starter_allowance = (
            starter_rate.allowance
            - starter_rate.reduction_rate * max_(0, applicable_amount - PA)
        )
        return max_(0, starter_allowance)


class trading_deduction(Variable):
    value_type = float
    entity = Person
    label = u"Self-employed earnings that are tax-free"
    definition_period = YEAR

    def formula(person, period, parameters):
        trading_allowance = parameters(
            period
        ).taxes.income_tax.allowances.trading_allowance
        return max_(0, min_(person("misc_income", period), trading_allowance))


class rental_deduction(Variable):
    value_type = float
    entity = Person
    label = u"Tax-free rental income"
    definition_period = YEAR

    def formula(person, period, parameters):
        rental_allowance = parameters(
            period
        ).taxes.income_tax.allowances.rental_allowance
        return max_(0, min_(person("rental_income", period), rental_allowance))


class dividend_deduction(Variable):
    value_type = float
    entity = Person
    label = u"Tax-free dividend income"
    definition_period = YEAR

    def formula(person, period, parameters):
        dividend_allowance = parameters(
            period
        ).taxes.income_tax.allowances.dividend_allowance
        return max_(
            0, min_(dividend_allowance, person("dividend_income", period))
        )


class dividend_income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Tax on dividends"
    definition_period = YEAR

    def formula(person, period, parameters):
        rates = parameters(period).taxes.income_tax.rates
        taxable_dividends = person("dividend_income", period) * 52 - person(
            "dividend_deduction", period
        )
        other_income = person("taxable_income", period)
        basic_amount = max_(
            0,
            min_(rates.uk.thresholds[1], other_income + taxable_dividends)
            - other_income,
        )
        higher_amount = max_(
            0,
            min_(rates.uk.thresholds[2], other_income + taxable_dividends)
            - other_income
            - rates.uk.thresholds[1],
        )
        additional_amount = higher_amount = max_(
            0,
            other_income
            + taxable_dividends
            - other_income
            - rates.uk.thresholds[2],
        )
        dividend_tax = (
            rates.dividend_rates.rates[0] * basic_amount
            + rates.dividend_rates.rates[1] * higher_amount
            + rates.dividend_rates.rates[2] * additional_amount
        )
        return dividend_tax


class is_higher_earner(Variable):
    value_type = float
    entity = Person
    label = u"Whether is the higher earner in the benefit unit"
    definition_period = YEAR

    def formula(person, period, parameters):
        higher_earner = (
            person("earned_income", period)
            > person.benunit.sum(
                person.benunit.members("earned_income", period)
            )
            / 2
        )
        equal_earners = (
            person("earned_income", period)
            == person.benunit.sum(
                person.benunit.members("earned_income", period)
            )
            / 2
        )
        return higher_earner + equal_earners * person(
            "is_benunit_head", period
        )


class CB_HITC(Variable):
    value_type = float
    entity = Person
    label = u"Child Benefit High-Income Tax Charge"
    definition_period = YEAR

    def formula(person, period, parameters):
        HITC = parameters(period).taxes.income_tax.CB_HITC
        income = person("taxable_income", period)
        phase = (
            min_(
                HITC.phase_out_end - HITC.phase_out_start,
                max_(0, income - HITC.phase_out_start),
            )
            / (HITC.phase_out_end - HITC.phase_out_start)
        )
        return (
            phase
            * person.benunit("child_benefit", period, options=[ADD])
            * person("is_higher_earner", period)
        )


class taxable_income_deductions(Variable):
    value_type = float
    entity = Person
    label = u"Income tax deductions"
    definition_period = YEAR

    def formula(person, period, parameters):
        DEDUCTIBLE = [
            "dividend_deduction",
            "rental_deduction",
            "trading_deduction",
            "savings_starter_allowance_deduction",
            "personal_savings_allowance_deduction",
            "personal_allowance_deduction",
            "marriage_allowance_deduction",
            "ISA_interest",
            "pension_deductions",
        ]
        total_deductions = add(person, period, DEDUCTIBLE)
        return max_(0, total_deductions)


class income_tax(Variable):
    value_type = float
    entity = Person
    label = u"Income Tax liability"
    definition_period = YEAR

    def formula(person, period, parameters):
        income_tax = parameters(period).taxes.income_tax
        applicable_amount = person("taxable_income", period) - person(
            "taxable_income_deductions", period
        )
        country = person.household("country", period)
        is_in_scotland = country == country.possible_values.SCOTLAND
        base_income_tax = where(
            is_in_scotland,
            income_tax.rates.scotland.calc(applicable_amount),
            income_tax.rates.uk.calc(applicable_amount),
        )
        additional_taxes = add(
            person, period, ["dividend_income_tax", "CB_HITC"]
        )
        return base_income_tax + additional_taxes


class total_tax(Variable):
    value_type = float
    entity = Person
    label = u"Income Tax and NI"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("income_tax", period) + person("NI", period)

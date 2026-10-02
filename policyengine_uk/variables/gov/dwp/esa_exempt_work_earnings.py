from policyengine_uk.model_api import *


class esa_exempt_work_earnings(Variable):
    value_type = float
    entity = Person
    label = "Weekly earnings for the ESA exempt work limits"
    documentation = (
        "A claimant's earnings in a week, which ESA Regs 2008 reg 45(2) and "
        "(4) compare with the exempt work earnings limits. They are worked "
        "out under the rules for calculating earnings for income-related ESA "
        "(DMG 41189; regs 92 to 99), and divided by 52. "
        "Employment (reg 96(3)): gross pay less the income tax and primary "
        "Class 1 contributions deducted from it and half the person's "
        "occupational and personal pension contributions. The regulation "
        "takes the tax actually deducted, which the model's inputs do not "
        "record; the model approximates it by the income tax on the pay taken "
        "as the lowest slice of the person's non-savings income, so tax on a "
        "pension, a taxable benefit, self-employment, property, savings or "
        "dividends never comes off the pay. A second job taxed at the basic "
        "rate through PAYE would leave lower net earnings than this. "
        "Self-employment (reg 98(3) and reg 99): the profit less a notional "
        "income tax at the basic rate (the Scottish basic rate for a Scottish "
        "taxpayer) on the profit above the personal allowance, notional "
        "Class 4 contributions at the main rate between the lower and upper "
        "profits limits, and half the personal pension contributions. The "
        "model gives personal pension contributions to self-employment when "
        "there is a profit and to employment otherwise. A loss in one "
        "employment is not set against earnings from another (reg 98(11)), "
        "so a self-employment loss counts as nil. Personal reliefs other "
        "than the personal allowance (reg 99(1)) are not modelled. Enter this "
        "variable directly for actual net earnings, for example where PAYE "
        "deducted a different amount or the regulations' averaging periods "
        "give a different figure."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/45",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/96",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/98",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/99",
        "https://assets.publishing.service.gov.uk/media/689db34d1fedc616bb13399c/dmg-ch-41.pdf",
    )

    def formula(person, period, parameters):
        income_tax = parameters(period).gov.hmrc.income_tax
        rates = income_tax.rates
        scottish = person("pays_scottish_income_tax", period)
        profit = max_(0, person("self_employment_income", period))
        personal_pension = person("personal_pension_contributions", period)
        personal_pension_from_profit = where(profit > 0, personal_pension, 0)

        # Employment, reg 96(3). Income tax on the pay as the lowest slice of
        # non-savings income: the part of earned_taxable_income left after
        # the person's other non-savings income is taken off the top.
        # earned_taxable_income is adjusted net income less the incomes and
        # allowances on the exclusions list.
        pay = person("employment_income", period)
        exclusions = list(income_tax.earned_taxable_income_exclusions)
        excluded_incomes = [
            variable
            for variable in exclusions
            if variable in income_tax.adjusted_net_income_components
        ]
        pay_in_base = (
            0
            if "taxable_employment_income" in exclusions
            else person("taxable_employment_income", period)
        )
        income_in_base = person("adjusted_net_income", period) - add(
            person, period, excluded_incomes
        )
        other_income = max_(0, income_in_base - pay_in_base)
        taxable_pay = max_(0, person("earned_taxable_income", period) - other_income)
        tax_on_pay = where(
            scottish,
            rates.scotland.rates.calc(taxable_pay),
            rates.uk.calc(taxable_pay),
        )
        # Tax reductions (for example the married couple's allowance) come
        # off the tax on pay first, as allowances do.
        reductions = add(person, period, income_tax.income_tax_subtractions)
        tax_on_pay = max_(0, tax_on_pay - reductions)
        pension_from_pay = (
            person("employee_pension_contributions", period)
            + personal_pension
            - personal_pension_from_profit
        )
        net_pay = max_(
            0,
            pay
            - tax_on_pay
            - person("ni_class_1_employee", period)
            - pension_from_pay / 2,
        )

        # Self-employment, reg 98(3) and reg 99. Reg 99(1): tax at the basic
        # rate (the first UK band; the second Scottish band, after the
        # starter rate) on the profit less the personal allowance.
        basic_rate = where(scottish, rates.scotland.rates.rates[1], rates.uk.rates[0])
        notional_tax = basic_rate * max_(
            0, profit - person("personal_allowance", period)
        )
        # Reg 99(3)(b): Class 4 at the main rate between the profits limits.
        notional_class_4 = person("ni_class_4_main", period)
        net_profit = max_(
            0,
            profit - notional_tax - notional_class_4 - personal_pension_from_profit / 2,
        )
        return (net_pay + net_profit) / WEEKS_IN_YEAR

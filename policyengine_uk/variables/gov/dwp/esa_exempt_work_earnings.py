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
        "takes the tax and contributions actually deducted, which the "
        "model's inputs do not record. The model approximates them on the "
        "pay alone. Income tax: the rates on the pay less employment "
        "expenses and employee pension contributions (net pay arrangements), "
        "above the personal and blind person's allowances, less the married "
        "couple's allowance reduction up to that tax. The allowances are the "
        "person's own, so other income can still reduce them through the "
        "personal allowance taper, but the tax on other income never comes "
        "off the pay, a self-employment loss cannot change it, and credits "
        "settled through a tax return (such as foreign tax credit relief) are "
        "not taken off it. Class 1: the main and additional primary rates on "
        "the pay between the primary threshold and the upper earnings limit "
        "and above it. Statutory sick, maternity and paternity pay are not "
        "earnings (reg 95(2)(b)), so they add neither to the pay nor to the "
        "tax and contributions taken off it. A second job taxed at the basic "
        "rate through PAYE would leave lower net earnings than this. "
        "Self-employment (reg 98(3) and reg 99): the profit less a notional "
        "income tax at the basic rate (the Scottish basic rate for a Scottish "
        "taxpayer) on the profit above the personal and blind person's "
        "allowances, notional Class 4 contributions at the main rate between "
        "the lower and upper profits limits, notional Class 2 contributions "
        "until 5 April 2024 (reg 99(3)(a)), and half the personal pension "
        "contributions. The model gives personal pension contributions to "
        "self-employment when there is a profit and to employment otherwise. "
        "A loss in one employment is not set against earnings from another "
        "(reg 98(11)), so a self-employment loss counts as nil. The notional "
        "National Insurance reads the model's Class 2 and Class 4 parameters "
        "for the year. The transferable (marriage) allowance and other "
        "reliefs reg 99(1) allows are not applied. Enter this variable directly for actual net "
        "earnings, for example where PAYE deducted a different amount or the "
        "regulations' averaging periods give a different figure."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/45",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/95",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/96",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/98",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/99",
        "https://assets.publishing.service.gov.uk/media/689db34d1fedc616bb13399c/dmg-ch-41.pdf",
    )

    def formula(person, period, parameters):
        p = parameters(period)
        income_tax = p.gov.hmrc.income_tax
        rates = income_tax.rates
        scottish = person("pays_scottish_income_tax", period)
        allowances = add(
            person, period, ["personal_allowance", "blind_persons_allowance"]
        )
        profit = max_(0, person("self_employment_income", period))
        personal_pension = person("personal_pension_contributions", period)
        personal_pension_from_profit = where(profit > 0, personal_pension, 0)
        employee_pension = person("employee_pension_contributions", period)

        # Employment, reg 96(3): PAYE and primary Class 1 on the pay alone.
        # Statutory sick, maternity and paternity pay are not earnings (reg
        # 95(2)(b)), so the shared taxable employment income and Class 1
        # base, which include them, are not used.
        pay = person("employment_income", period)
        taxable_pay = max_(0, pay - person("employment_deductions", period))
        taxable_pay_after_pension = max_(
            0, taxable_pay - min_(employee_pension, taxable_pay)
        )
        taxed_pay = max_(0, taxable_pay_after_pension - allowances)
        tax_on_pay = where(
            scottish,
            rates.scotland.rates.calc(taxed_pay),
            rates.uk.calc(taxed_pay),
        )
        # The married couple's allowance reduction, given through the tax
        # code, up to the tax on the pay itself. The shared capped_mcad is
        # capped against the person's whole liability, which other income
        # and losses move.
        mca_reduction = person("married_couples_allowance_deduction", period)
        tax_on_pay = max_(0, tax_on_pay - mca_reduction)
        nics = p.gov.hmrc.national_insurance
        class_1 = nics.class_1
        primary_threshold = class_1.thresholds.primary_threshold * WEEKS_IN_YEAR
        upper_earnings_limit = class_1.thresholds.upper_earnings_limit * WEEKS_IN_YEAR
        pay_above_upper_limit = max_(0, pay - upper_earnings_limit)
        class_1_on_pay = person("ni_liable", period) * (
            class_1.rates.employee.main
            * (max_(0, pay - primary_threshold) - pay_above_upper_limit)
            + class_1.rates.employee.additional * pay_above_upper_limit
        )
        pension_from_pay = (
            employee_pension + personal_pension - personal_pension_from_profit
        )
        net_pay = max_(
            0,
            pay - tax_on_pay - class_1_on_pay - pension_from_pay / 2,
        )

        # Self-employment, reg 98(3) and reg 99. Reg 99(1): tax at the basic
        # rate on the profit less the personal reliefs. The UK basic rate is
        # the first UK band; the Scottish basic rate is the first Scottish
        # band, or the second once the starter rate came in on 6 April 2018.
        scottish_rates = rates.scotland.rates.rates
        scottish_basic_rate = (
            scottish_rates[1] if period.start.year >= 2018 else scottish_rates[0]
        )
        basic_rate = where(scottish, scottish_basic_rate, rates.uk.rates[0])
        notional_tax = basic_rate * max_(0, profit - allowances)
        # Reg 99(3)(b): Class 4 at the main rate between the profits limits.
        notional_class_4 = person("ni_class_4_main", period)
        # Reg 99(3)(a), until 5 April 2024: Class 2 at the weekly rate unless
        # the profit is below the small profits threshold or, from 6 April
        # 2022, at or below the lower profits threshold (SSCBA 1992 s.11(4),
        # which the model takes as the Class 4 lower profits limit).
        class_2_rule = p.gov.dwp.ESA.income.self_employment_class_2
        class_2_due = where(
            class_2_rule.above_lower_profits_threshold,
            profit > nics.class_4.thresholds.lower_profits_limit,
            profit >= nics.class_2.small_profits_threshold,
        )
        notional_class_2 = (
            class_2_rule.deducted
            * class_2_due
            * person("ni_liable", period)
            * nics.class_2.flat_rate
            * WEEKS_IN_YEAR
        )
        net_profit = max_(
            0,
            profit
            - notional_tax
            - notional_class_4
            - notional_class_2
            - personal_pension_from_profit / 2,
        )
        return (net_pay + net_profit) / WEEKS_IN_YEAR

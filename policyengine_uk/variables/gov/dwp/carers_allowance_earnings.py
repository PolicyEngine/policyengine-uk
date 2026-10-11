from policyengine_uk.model_api import *


class carers_allowance_earnings(Variable):
    value_type = float
    entity = Person
    label = "earnings for the Carer's Allowance earnings limit"
    documentation = (
        "Net earnings from employment and self-employment, as the Carer's "
        "Allowance gainful-employment test counts them (Computation of "
        "Earnings Regulations 1996), less half of the person's pension "
        "contributions. A trading loss counts as nil.\n\n"
        "Employment (reg. 10(4)): gross pay less the income tax and primary "
        "Class 1 contributions deducted from it. The law deducts the tax "
        "actually withheld; the model approximates it as the tax PAYE would "
        "take on a standard code if the pay were the person's only income "
        "(pay less net-pay pension contributions and the personal allowance, "
        "at rest-of-UK or Scottish rates). That also avoids a circularity, "
        "since Carer's Allowance is itself taxable, and makes unearned income "
        "irrelevant here by assumption.\n\n"
        "Self-employment (regs. 13(4) and 14): trading profit less a notional "
        "income tax at the basic rate (the Scottish basic rate for a Scottish "
        "taxpayer) on the profit above whatever personal allowance the pay "
        "leaves unused, and Class 4 contributions at the main rate on the "
        "profit between the lower and upper profits limits. Regulation 14 "
        "deducts no Class 2 contribution.\n\n"
        "Not modelled: the deduction for care charges (Schedule 3, up to half "
        "of net earnings) and the Schedule 1 disregards, so this can overstate "
        "earnings for a carer who pays for care while at work."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Benefit (Computation of Earnings) Regulations 1996 reg. 10(4)",
            href="https://www.legislation.gov.uk/uksi/1996/2745/regulation/10",
        ),
        dict(
            title="Social Security Benefit (Computation of Earnings) Regulations 1996 reg. 13",
            href="https://www.legislation.gov.uk/uksi/1996/2745/regulation/13",
        ),
        dict(
            title="Social Security Benefit (Computation of Earnings) Regulations 1996 reg. 14",
            href="https://www.legislation.gov.uk/uksi/1996/2745/regulation/14",
        ),
    ]

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc
        income_tax = p.income_tax
        class_4 = p.national_insurance.class_4
        scottish = person("pays_scottish_income_tax", period)
        personal_allowance = income_tax.allowances.personal_allowance.amount

        # Employment: PAYE on the pay alone (reg. 10(4)(a)).
        pay = person("employment_income", period)
        taxable_pay = max_(0, pay - person("employee_pension_contributions", period))
        pay_tax = where(
            scottish,
            income_tax.rates.scotland.rates.calc(
                max_(0, taxable_pay - personal_allowance)
            ),
            income_tax.rates.uk.calc(max_(0, taxable_pay - personal_allowance)),
        )
        primary_class_1 = person("ni_class_1_employee", period)

        # Self-employment: notional basic-rate tax and main-rate Class 4
        # (reg. 14(1)-(2)), with one set of personal reliefs, used by the pay
        # first.
        profit = max_(0, person("self_employment_income", period))
        unused_allowance = max_(0, personal_allowance - taxable_pay)
        basic_rate = where(
            scottish,
            income_tax.rates.scotland.rates.rates[1],
            income_tax.rates.uk.rates[0],
        )
        trading_tax = basic_rate * max_(0, profit - unused_allowance)
        trading_class_4 = class_4.rates.main * max_(
            0,
            min_(profit, class_4.thresholds.upper_profits_limit)
            - class_4.thresholds.lower_profits_limit,
        )

        half_pension_contributions = 0.5 * person("pension_contributions", period)
        return max_(
            0,
            pay
            - pay_tax
            - primary_class_1
            + profit
            - trading_tax
            - trading_class_4
            - half_pension_contributions,
        )

from policyengine_uk.model_api import *


class carers_allowance_earnings(Variable):
    value_type = float
    entity = Person
    label = "earnings for the Carer's Allowance earnings limit"
    documentation = (
        "Net earnings from employment and self-employment, as the Carer's "
        "Allowance gainful-employment test counts them: gross pay and trading "
        "profit less the income tax and National Insurance deducted from them "
        "and half of the person's pension contributions. A trading loss counts "
        "as nil. The income tax is the tax PAYE would deduct if the earnings "
        "were the person's only income: earnings less net-pay pension "
        "contributions and the standard personal allowance, at the person's "
        "rest-of-UK or Scottish rates. That is the tax deducted from pay, and "
        "it avoids a circularity, since Carer's Allowance is itself taxable. "
        "The deduction for care charges (Computation of Earnings Regulations "
        "1996 Schedule 3, up to half of net earnings) and the Schedule 1 "
        "disregards are not modelled, so this can overstate earnings for a "
        "carer who pays for care while at work."
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
    ]

    def formula(person, period, parameters):
        income_tax = parameters(period).gov.hmrc.income_tax
        employment = person("employment_income", period)
        trading = max_(0, person("self_employment_income", period))
        net_pay_pension = person("employee_pension_contributions", period)
        taxable = max_(
            0,
            employment
            + trading
            - net_pay_pension
            - income_tax.allowances.personal_allowance.amount,
        )
        tax = where(
            person("pays_scottish_income_tax", period),
            income_tax.rates.scotland.rates.calc(taxable),
            income_tax.rates.uk.calc(taxable),
        )
        national_insurance = person("uc_national_insurance_on_earnings", period)
        half_pension_contributions = 0.5 * person("pension_contributions", period)
        return max_(
            0,
            employment
            + trading
            - tax
            - national_insurance
            - half_pension_contributions,
        )

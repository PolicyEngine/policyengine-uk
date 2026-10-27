from policyengine_uk.model_api import *
from policyengine_uk.utils.class_2 import class_2_contribution_weeks, class_2_liable
from policyengine_uk.utils.pence import stored_pence


def _earned(amount):
    """Pay or profit in whole pence, a fraction of a penny disregarded (reg. 5)."""
    return np.floor(stored_pence(amount))


def _deducted(pence):
    """A deduction in whole pence, a fraction of a penny counted as a penny
    (reg. 5). The float64 arithmetic that produces it is exact to far less
    than a millionth of a penny, so a deduction within a millionth of a penny
    above a whole penny is that penny."""
    return np.ceil(pence - 1e-6)


class carers_allowance_earnings(Variable):
    value_type = float
    entity = Person
    label = "earnings for the Carer's Allowance earnings limit"
    documentation = (
        "Net earnings from employment and self-employment, as the Carer's "
        "Allowance gainful-employment test counts them (Computation of "
        "Earnings Regulations 1996), less a share of the person's pension "
        "contributions: one half in law (regs. 10(4)(b) and 13(4)(c)), read "
        "from gov.dwp.carers_allowance.pension_contribution_deduction_rate. "
        "A trading loss counts as nil.\n\n"
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
        "taxpayer) on the profit above the full personal allowance, and Class 4 "
        "contributions, where payable, at the main rate on the profit between "
        "the lower and upper profits limits. Regulation 14(1) deducts the personal reliefs "
        "the claimant is entitled to, with no reduction for any allowance the "
        "pay uses, and capital expenditure is not deducted (reg. 13(6)(a)). "
        "Until 6 April 2024 reg. 14(2)(a) also deducted the Class 2 "
        "contributions payable on the chargeable profit; that paragraph was "
        "omitted with compulsory Class 2, whose flat rate is nil from "
        "2024-25. Class 2 uses ni_liable's annual approximation of the "
        "exemption after the week State Pension age is reached. Class 4 uses "
        "ni_class_4_liable: reaching State Pension age during the tax year "
        "leaves that year's contributions payable.\n\n"
        "A fraction of a penny counts in the claimant's favour (reg. 5): pay "
        "and profit are taken down to a whole penny and each deduction up to "
        "one, so net earnings are whole pence. The pence are worked in double "
        "precision from the whole pence each amount was entered as, since the "
        "model stores amounts in single precision, which holds most sums of "
        "money only to within a fraction of a penny.\n\n"
        "Not modelled: the deduction for care charges (Schedule 3, up to half "
        "of net earnings) and the Schedule 1 disregards, so this can overstate "
        "earnings for a carer who pays for care while at work."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Social Security Benefit (Computation of Earnings) Regulations 1996 reg. 5",
            href="https://www.legislation.gov.uk/uksi/1996/2745/regulation/5",
        ),
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
        dict(
            title="Social Security Contributions and Benefits Act 1992 s. 11(7)",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/11",
        ),
        dict(
            title="Social Security (Contributions) Regulations 2001 reg. 91(a)",
            href="https://www.legislation.gov.uk/uksi/2001/1004/regulation/91",
        ),
    ]

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc
        income_tax = p.income_tax
        class_4 = p.national_insurance.class_4
        scottish = person("pays_scottish_income_tax", period)
        personal_allowance = income_tax.allowances.personal_allowance.amount

        # Work in float64 pence from the whole pence each amount was entered
        # as (stored_pence), taking pay and profit down to a whole penny and
        # each deduction up to one (reg. 5). Scales and thresholds are in
        # pounds.

        # Employment: PAYE on the pay alone (reg. 10(4)(a)).
        pay = _earned(person("employment_income", period))
        employee_pension = stored_pence(
            person("employee_pension_contributions", period)
        )
        taxable_pay = max_(0, pay - employee_pension) / 100
        pay_tax = where(
            scottish,
            income_tax.rates.scotland.rates.calc(
                max_(0, taxable_pay - personal_allowance)
            ),
            income_tax.rates.uk.calc(max_(0, taxable_pay - personal_allowance)),
        )
        # Computed in float32 by another variable: a whole-penny amount that
        # comes back more than half a step out counts as a penny more, in the
        # claimant's favour.
        primary_class_1 = stored_pence(person("ni_class_1_employee", period))

        # Self-employment: notional basic-rate tax and main-rate Class 4
        # (reg. 14(1)-(2)). The tax is on the profit as if it were the only
        # income, less the full personal allowance.
        profit = _earned(max_(0, person("self_employment_income", period)))
        profit_pounds = profit / 100
        # The basic rate is the first band of the rest-of-UK scale (ITA 2007
        # s. 6(2)). The Scottish basic rate is the second bracket of the
        # Scottish scale, after the starter rate; read it from the parameter
        # tree, which keeps the null starter bracket of years before 2018-19 in
        # place. The scale at an instant drops null brackets, so its index 1
        # was the higher rate in 2016-17 and 2017-18.
        scottish_scale = person.simulation.tax_benefit_system.parameters.gov.hmrc.income_tax.rates.scotland.rates
        basic_rate = where(
            scottish,
            scottish_scale.brackets[1].rate(period.start),
            income_tax.rates.uk.rates[0],
        )
        trading_tax = basic_rate * max_(0, profit_pounds - personal_allowance)
        trading_class_4 = (
            person("ni_class_4_liable", period)
            * class_4.rates.main
            * max_(
                0,
                min_(profit_pounds, class_4.thresholds.upper_profits_limit)
                - class_4.thresholds.lower_profits_limit,
            )
        )
        # Reg. 14(2)(a), omitted from 6 April 2024: the Class 2 contributions
        # payable on the chargeable profit (SSCBA 1992 s. 11), on the
        # profit itself rather than ni_class_2's base after capital
        # allowances. The flat rate is nil from 2024-25.
        class_2 = p.national_insurance.class_2
        trading_class_2 = (
            person("ni_liable", period)
            * class_2_liable(profit_pounds, class_2)
            * class_2.flat_rate
            * class_2_contribution_weeks(period.start.year)
        )

        # Regs. 10(4)(b) and 13(1)(b)(ii), (4)(c) and (10)(b): one half of
        # pension contributions and premiums. The contributions are those
        # pension_contributions adds, summed here in float64 pence.
        pension_share = parameters(
            period
        ).gov.dwp.carers_allowance.pension_contribution_deduction_rate
        contributions = sum(
            stored_pence(person(program, period))
            for program in p.pensions.pensions_programs
        )
        pension_deduction = pension_share * contributions
        net = (
            pay
            - _deducted(pay_tax * 100)
            - _deducted(primary_class_1)
            + profit
            - _deducted(trading_tax * 100)
            - _deducted(trading_class_4 * 100)
            - _deducted(trading_class_2 * 100)
            - _deducted(pension_deduction)
        )
        return max_(0, net) / 100

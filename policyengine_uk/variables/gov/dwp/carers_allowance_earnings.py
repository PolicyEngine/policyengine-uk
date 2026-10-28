import functools
import types

from policyengine_uk.model_api import *
from policyengine_uk.utils.class_2 import class_2_contribution_weeks, class_2_liable
from policyengine_uk.utils.pence import (
    amount_pence,
    neutralized,
    stored_pence,
    supplied,
)
from policyengine_uk.variables.gov.hmrc.national_insurance.class_1.ni_class_1_employee import (
    ni_class_1_employee,
)
from policyengine_uk.variables.gov.hmrc.national_insurance.class_1.ni_class_1_employee_additional import (
    ni_class_1_employee_additional,
)
from policyengine_uk.variables.gov.hmrc.national_insurance.class_1.ni_class_1_employee_primary import (
    ni_class_1_employee_primary,
)

# The model's Class 1 variables, whose calculation _primary_class_1 works out
# exactly.
_CLASS_1 = (
    ni_class_1_employee,
    ni_class_1_employee_primary,
    ni_class_1_employee_additional,
)
# How their formulas read the amounts they depend on, which _primary_class_1
# reads for the year: NI income for a month is a twelfth of the year's, and
# liability and directorship for a month are the year's.
_CLASS_1_READS = (
    ("ni_class_1_income", YEAR, FLOW),
    ("ni_liable", YEAR, STOCK),
    ("is_full_year_category_a_director", YEAR, STOCK),
)


def _earned(pence):
    """Pay or profit in whole pence, a fraction of a penny disregarded (reg. 5)."""
    return np.floor(pence)


def _deducted(pence):
    """A deduction in whole pence, a fraction of a penny counted as a penny
    (reg. 5). The float64 arithmetic that produces it is exact to far less
    than a millionth of a penny, so a deduction within a millionth of a penny
    above a whole penny is that penny."""
    return np.ceil(pence - 1e-6)


@functools.cache
def _model_class_1():
    """The model's Class 1 variables, as the model defines them."""
    return tuple(variable() for variable in _CLASS_1)


def _how_calculated(variable):
    """What, besides its formulas, decides how policyengine-core calculates
    ``variable``."""
    return (
        variable.entity.key,
        variable.definition_period,
        variable.value_type,
        variable.quantity_type,
        variable.default_value,
        variable.end,
        variable.adds,
        variable.subtracts,
        variable.defined_for,
        variable.is_neutralized,
    )


def _global_names(code):
    """The global names ``code``, and the code nested in it, can read."""
    names = set(code.co_names)
    for constant in code.co_consts:
        if isinstance(constant, types.CodeType):
            names |= _global_names(constant)
    return names


def _same_formula(formula, model_formula):
    """Whether ``formula`` calculates as ``model_formula`` does: the same
    code, reading the same values of the globals it names, with the same
    defaults and closure. Either may be None, for no formula."""
    if formula is None or model_formula is None:
        return formula is model_formula
    absent = object()
    try:
        cells = [
            (cell.cell_contents, model_cell.cell_contents)
            for cell, model_cell in zip(
                formula.__closure__ or (), model_formula.__closure__ or ()
            )
        ]
    except ValueError:
        # An empty cell.
        return False
    return (
        formula.__code__ == model_formula.__code__
        and formula.__defaults__ == model_formula.__defaults__
        and formula.__kwdefaults__ == model_formula.__kwdefaults__
        and all(value is model_value for value, model_value in cells)
        and all(
            formula.__globals__.get(name, absent)
            is model_formula.__globals__.get(name, absent)
            for name in _global_names(formula.__code__)
        )
    )


def _class_1_calculated(person, period):
    """Whether policyengine-core calculated ni_class_1_employee for each
    month of ``period`` as the model does: no reform changed how it or its
    primary and additional parts are calculated in those months (their
    formulas, the dates the formulas apply from and to, how the parts are
    summed and masked, neutralization or abolition) or how the formulas read
    the amounts they depend on, and no month of any of them was supplied as
    an input or stored by a scenario."""
    simulation = person.simulation
    variables = simulation.tax_benefit_system.variables
    for name, definition_period, quantity_type in _CLASS_1_READS:
        variable = variables.get(name)
        if (
            variable is None
            or variable.definition_period != definition_period
            or variable.quantity_type != quantity_type
        ):
            return False
    for model_variable in _model_class_1():
        name = model_variable.name
        variable = variables.get(name)
        if variable is None or _how_calculated(variable) != _how_calculated(
            model_variable
        ):
            return False
        for month in period.get_subperiods(MONTH):
            if (
                neutralized(simulation, variable, month)
                or supplied(person, name, month)
                or not _same_formula(
                    variable.get_formula(month), model_variable.get_formula(month)
                )
            ):
                return False
    return True


def _primary_class_1(person, period, parameters):
    """ni_class_1_employee in float64 pence.

    The model works out each month's Class 1 in float32 and sums the twelve,
    which can leave a whole-penny total further from it than stored_pence
    recovers: £175.56 (8% of £14,764.46 less £12,569.96) is stored as
    175.5600128, and rounding that up would deduct a penny too much. So where
    the model calculated it with its own formula, the formula (the primary
    and additional parts, month by month) is worked exactly on the year's NI
    income. Otherwise, the deduction is the amount stored for each month,
    summed exactly (amount_pence): one supplied as an input, for the year or
    month by month, or calculated under a reform that changes the formula,
    is the amount deducted (reg. 10(4)(a)), whatever the formula would give.
    """
    stored = person("ni_class_1_employee", period)
    deducted = amount_pence(person, "ni_class_1_employee", period)
    if not _class_1_calculated(person, period):
        return deducted
    income = amount_pence(person, "ni_class_1_income", period)
    director = person("is_full_year_category_a_director", period)
    exact = 0
    for month in period.get_subperiods(MONTH):
        class_1 = parameters(month).gov.hmrc.national_insurance.class_1
        scale = class_1.employee_scale
        # Weekly thresholds in pounds, as monthly amounts in pence.
        primary_threshold = (
            scale.components[1].threshold * WEEKS_IN_YEAR * 100 / MONTHS_IN_YEAR
        )
        upper_limit = (
            scale.components[2].threshold * WEEKS_IN_YEAR * 100 / MONTHS_IN_YEAR
        )
        monthly = income / MONTHS_IN_YEAR
        above_upper = max_(monthly - upper_limit, 0)
        contribution = (
            scale.components[1].rate
            * (max_(monthly - primary_threshold, 0) - above_upper)
            + scale.components[2].rate * above_upper
        )
        directors = class_1.directors.full_year_category_a_2022_23
        if directors.in_effect:
            # Annual thresholds in pounds.
            rates = directors.employee_scale.rates
            thresholds = [t * 100 for t in directors.employee_scale.thresholds]
            annual = rates[1] * min_(
                max_(income - thresholds[1], 0), thresholds[2] - thresholds[1]
            ) + rates[2] * max_(income - thresholds[2], 0)
            contribution = where(director, annual / MONTHS_IN_YEAR, contribution)
        exact = exact + contribution
    exact = exact * person("ni_liable", period)
    # The twelve float32 months and their sum err by less than one float32
    # step of the year's NI income plus 64 steps of the contribution. A
    # larger disagreement would mean the formula worked out here no longer
    # matches the model's, and then the amount calculated is deducted.
    tolerance = 100 * (
        np.spacing(np.abs(person("ni_class_1_income", period))).astype(np.float64)
        + 64 * np.spacing(np.abs(stored)).astype(np.float64)
    )
    agrees = np.abs(np.asarray(stored, dtype=np.float64) * 100 - exact) <= tolerance
    return where(agrees, exact, deducted)


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
        "and profit are taken down to a whole penny, and the calculated "
        "deductions (notional tax, Class 4 and Class 2, and half of pension "
        "contributions) up to one. PAYE and Class 1 are in law the amounts "
        "actually deducted, which are whole pence; the model's figures for "
        "them are rounded up as well, a fraction counting in the claimant's "
        "favour. Net earnings are therefore whole pence. They are worked in "
        "double precision from the whole pence each amount was entered as, "
        "since the model stores amounts in single precision, which holds most "
        "sums of money only to within a fraction of a penny; an amount the "
        "model sums from others (pay, pension contributions, NI income) is the "
        "exact sum of its parts, read the same way, whether or not the "
        "simulation's cache policy keeps it. Class 1, which the model sums "
        "from twelve single-precision months, is worked out again from its "
        "formula where the model calculated it with that formula; Class 1 "
        "entered as an input (for the year or month by month), or calculated "
        "under a reform of its formula or of how it reads NI income, is "
        "deducted as entered or calculated, its months summed exactly and an "
        "amount entered for the year recovered in whole pence. The model holds each pension programme as one "
        "amount for the year, so half of the year's total is deducted, rounded "
        "up once.\n\n"
        "The Scottish Carer Support Payment reads these earnings too "
        "(carer_support_payment_pre_couple_limit): SSI 2023/302 Schedule 2 has "
        "the same rounding rule (para. 4) and net earnings and profit (paras. 9 "
        "and 12).\n\n"
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
        # as, and sums of them worked exactly (amount_pence), taking pay and
        # profit down to a whole penny and each deduction up to one (reg. 5
        # for the calculated deductions; for PAYE and Class 1, which the law
        # takes as deducted, the same rounding in the claimant's favour).
        # Scales and thresholds are in pounds.

        # Employment: PAYE on the pay alone (reg. 10(4)(a)).
        pay = _earned(amount_pence(person, "employment_income", period))
        employee_pension = amount_pence(
            person, "employee_pension_contributions", period
        )
        taxable_pay = max_(0, pay - employee_pension) / 100
        pay_tax = where(
            scottish,
            income_tax.rates.scotland.rates.calc(
                max_(0, taxable_pay - personal_allowance)
            ),
            income_tax.rates.uk.calc(max_(0, taxable_pay - personal_allowance)),
        )
        primary_class_1 = _primary_class_1(person, period, parameters)

        # Self-employment: notional basic-rate tax and main-rate Class 4
        # (reg. 14(1)-(2)). The tax is on the profit as if it were the only
        # income, less the full personal allowance.
        profit = _earned(
            stored_pence(max_(0, person("self_employment_income", period)))
        )
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
            * class_4.contribution_scale.components[1].rate
            * max_(
                0,
                min_(profit_pounds, class_4.contribution_scale.components[2].threshold)
                - class_4.contribution_scale.components[1].threshold,
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
        # pension contributions and premiums. The model holds each programme
        # as one amount for the year, not the payments the law halves one by
        # one, so the half is of the year's total, rounded up once. The total
        # is pension_contributions, whether entered or summed from its
        # programmes (and theirs).
        pension_share = parameters(
            period
        ).gov.dwp.carers_allowance.pension_contribution_deduction_rate
        contributions = amount_pence(person, "pension_contributions", period)
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

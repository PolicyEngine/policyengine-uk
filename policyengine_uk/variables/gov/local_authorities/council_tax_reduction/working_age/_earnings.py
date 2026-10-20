from policyengine_uk.model_api import *
from policyengine_uk.utils.class_2 import class_2_contribution_weeks, class_2_liable
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_wales_scheme,
)

STATUTORY_PAY = [
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
]

# Taxable income in earned_income_tax's base, other than earnings, that the
# working-age schemes do not count as unearned income. Property income is
# outside that base (property_income_tax), as are savings and dividends.
NOT_COUNTED_TAXABLE_UNEARNED = ["scottish_carer_supplement"]


def _self_employed_net_profit(person, period, parameters):
    """Net profit of a self-employed earner without Universal Credit, before
    the pension deduction.

    The profit less an amount for income tax and contributions that the
    schemes prescribe, not the tax actually paid (SSI 2012/303 regs 37(3)(b)
    and 38, applied by SSI 2021/249 reg 51(9); WSI 2013/3029 Sch 6 paras 24(3)
    and 25):
    - income tax at the basic rate on the profit less the personal allowance,
      as if the profit were the only income (Wales also allows the blind
      person's allowance; the marriage and married couple's allowances are not
      modelled);
    - Class 4 at the main rate on the profit between the profits limits;
    - until 5 April 2024, Class 2 at the weekly rate where it was payable.
    A trading loss counts as nil, and is not set against other earnings
    (SSI 2012/303 reg 37(10)).
    """
    p = parameters(period).gov.hmrc
    income_tax = p.income_tax
    class_4 = p.national_insurance.class_4
    class_2 = p.national_insurance.class_2
    profit = max_(0, person("self_employment_income", period))
    wales = is_wales_scheme(person.household("country", period))
    allowances = income_tax.allowances.personal_allowance.amount + where(
        wales, person("blind_persons_allowance", period), 0
    )
    # The basic rate is the first band of the rest-of-UK scale (ITA 2007
    # s. 6(2)) and the second of the Scottish scale, after the starter rate,
    # as in carers_allowance_earnings.
    scottish_scale = person.simulation.tax_benefit_system.parameters.gov.hmrc.income_tax.rates.scotland.rates
    basic_rate = where(
        person("pays_scottish_income_tax", period),
        scottish_scale.brackets[1].rate(period.start),
        income_tax.rates.uk.rates[0],
    )
    notional_tax = basic_rate * max_(0, profit - allowances)
    notional_class_4 = (
        person("ni_class_4_liable", period)
        * class_4.rates.main
        * max_(
            0,
            min_(profit, class_4.thresholds.upper_profits_limit)
            - class_4.thresholds.lower_profits_limit,
        )
    )
    # Omitted from 6 April 2024 (SI 2024/377); the flat rate is nil from
    # 2024-25.
    notional_class_2 = (
        person("ni_liable", period)
        * class_2_liable(profit, class_2)
        * class_2.flat_rate
        * class_2_contribution_weeks(period.start.year)
    )
    return max_(0, profit - notional_tax - notional_class_4 - notional_class_2)


def working_age_earnings(person, period, parameters):
    """Net earnings and the employed part of them, per person.

    With an award of Universal Credit:
    - Wales uses the Secretary of State's figure for the award, which is the
      model's Universal Credit earned income before the work allowance, after
      the minimum income floor (WSI 2013/3029 Sch 6 para 9);
    - Scotland calculates earnings on the Universal Credit basis (SSI 2021/249
      regs 49 and 51(2)): employed earnings including statutory sick,
      maternity and paternity pay, and self-employed profit, less the income
      tax and National Insurance paid in respect of them and relievable
      pension contributions, with no minimum income floor.
    Without Universal Credit:
    - employed earnings are pay and statutory sick, maternity and paternity
      pay, less the income tax and primary Class 1 contributions in respect of
      the employment (SSI 2021/249 reg 50(3)(a); WSI 2013/3029 Sch 6 para
      15(3)(a)). The tax is the model's Universal Credit split of the person's
      income tax (earnings taken as the lowest slice of non-savings income),
      less the part on any trade, shared pro rata with miscellaneous income;
    - self-employed earnings are the net profit with the prescribed notional
      tax and contributions (_self_employed_net_profit);
    - one half of pension contributions comes off
      (council_tax_reduction_pension_contribution_deduction_rate).
    Voluntary Class 3 contributions never come off.
    Returns (net earnings, net employed earnings).
    """
    has_universal_credit = person.benunit(
        "council_tax_reduction_working_age_has_universal_credit", period
    )
    wales = is_wales_scheme(person.household("country", period))
    wales_universal_credit = person("uc_individual_earned_income", period)
    scotland_universal_credit = person("uc_individual_earned_income_before_mif", period)

    employment = person("employment_income", period) + add(
        person, period, STATUTORY_PAY
    )
    miscellaneous = max_(0, person("taxable_miscellaneous_income", period))
    employment_tax_and_national_insurance = (
        person("uc_income_tax_on_earnings", period)
        - person("uc_income_tax_on_trade", period)
        + person("uc_national_insurance_on_earnings", period)
        - person("uc_national_insurance_on_trade", period)
    )
    employment_share = np.divide(
        employment,
        employment + miscellaneous,
        out=np.zeros_like(employment, dtype=float),
        where=(employment + miscellaneous) > 0,
    )
    employed = max_(
        0, employment - employment_tax_and_national_insurance * employment_share
    )
    self_employed = _self_employed_net_profit(person, period, parameters)
    pension_rate = person.benunit(
        "council_tax_reduction_pension_contribution_deduction_rate", period
    )
    pension = pension_rate * person("pension_contributions", period)
    legacy = max_(0, employed + self_employed - pension)
    legacy_employed = np.divide(
        legacy * employed,
        employed + self_employed,
        out=np.zeros_like(legacy, dtype=float),
        where=(employed + self_employed) > 0,
    )

    universal_credit = where(wales, wales_universal_credit, scotland_universal_credit)
    # The £17.10 additional disregard, the only reader of the employed part,
    # does not apply with Universal Credit.
    net = where(has_universal_credit, universal_credit, legacy)
    net_employed = where(has_universal_credit, 0, legacy_employed)
    return net, net_employed


def working_age_unearned_income_tax(person, period):
    """Income tax on the person's counted taxable unearned income.

    earned_income_tax is the tax on non-savings income other than property
    income: earnings, pensions and taxable social security benefits. Less the
    tax on earnings (uc_income_tax_on_earnings, earnings being the lowest
    slice), the rest is tax on pensions and benefits, shared pro rata with the
    taxable ones the schemes do not count (the Scottish Carer Supplement).
    """
    other_non_savings_tax = max_(
        0,
        person("earned_income_tax", period)
        - person("uc_income_tax_on_earnings", period),
    )
    base = add(
        person, period, ["taxable_pension_income", "taxable_social_security_income"]
    )
    not_counted = add(person, period, NOT_COUNTED_TAXABLE_UNEARNED)
    counted_share = np.divide(
        max_(0, base - not_counted),
        base,
        out=np.ones_like(base, dtype=float),
        where=base > 0,
    )
    return other_non_savings_tax * counted_share

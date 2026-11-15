"""Income tax on a person's earnings, as Universal Credit deducts it.

Shared by uc_income_tax_on_earnings and uc_income_tax_on_trade, so both
take the same slice of the same tax computation.
"""

from policyengine_core.model_api import add, max_, where

from policyengine_uk.utils.income_tax import (
    calc_income_tax_with_gift_aid,
    first_extended_scottish_threshold,
)
from policyengine_uk.utils.income_tax_allocation import default_order_deductions


def earnings_tax_reductions(person, period, parameters):
    """The Step 6 tax reductions that come off the tax on earnings first.

    All of them except the finance-cost reduction, which comes off the tax on
    property income first, so only the part larger than that tax counts here.
    """
    income_tax = parameters(period).gov.hmrc.income_tax
    reductions = add(
        person,
        period,
        [
            variable
            for variable in income_tax.step_6_tax_reductions
            if variable != "property_finance_cost_relief"
        ],
    )
    return reductions + max_(
        0,
        person("property_finance_cost_relief", period)
        - person("property_income_tax", period),
    )


def uc_income_tax_on_earnings_slice(person, period, parameters, include_trade=True):
    """Income tax on the person's earnings taken as the lowest slice of income.

    With ``include_trade`` false, the slice is the person's employment and
    miscellaneous earnings alone, below their trading profits: the tax they
    would pay on those earnings if they had no trade, as PAYE codes give the
    personal allowance to the employment first.
    """
    # Reg. 55(5)(b) deducts income tax paid by the person "in respect of
    # the employment" and reg. 57(2) step 3 income tax paid "in respect
    # of any trade". Neither says how to split a person's tax when they
    # also have other income. The helper takes earnings as the lowest
    # slice of their non-savings income, after the allowances set against
    # non-savings income first: savings and dividends sit above earnings
    # and other non-savings income (as in ITA 2007 s. 16), property
    # income above the rest of it (as in s. 16A from 2027-28), and other
    # non-savings income (private pensions, State Pension, taxable
    # benefits) above earnings. So tax on other income never comes off
    # earnings. Under RTI, DWP deducts the PAYE actually taken on the job,
    # which can include tax on a State Pension coded against it; the
    # model leaves that out.
    p = parameters(period)
    income_tax = p.gov.hmrc.income_tax
    # earned_taxable_income is net income less the incomes and
    # allowances on the exclusions list. Read that list, so a reform
    # that changes it (for example one that exempts pensions) is
    # followed here.
    exclusions = list(income_tax.earned_taxable_income_exclusions)
    excluded_incomes = [
        variable
        for variable in exclusions
        if variable in income_tax.adjusted_net_income_components
    ]
    earnings_components = ["taxable_employment_income", "taxable_miscellaneous_income"]
    if include_trade:
        earnings_components.append("taxable_self_employment_income")
    # Match the gross earnings in uc_individual_earned_income_before_mif.
    bi = p.gov.contrib.ubi_center.basic_income.interactions
    if bi.include_in_means_tests and bi.include_in_taxable_income:
        earnings_components.append("basic_income")
    earnings = add(
        person,
        period,
        [variable for variable in earnings_components if variable not in exclusions],
    )
    # The slice follows the order non-savings, savings, dividends, not the
    # least-tax share of the reliefs and allowances (ITA 2007 s. 25(2)):
    # the model follows PAYE coding, which sets the allowances against the
    # job; moving them onto savings or dividends to lower the year's tax
    # would otherwise raise the tax on earnings. So the earnings slice reads
    # the old order's deductions, and more savings or dividends raise it
    # only by taking away a Step 6 tax reduction, as when they fail a
    # Marriage Allowance recipient on the rate test.
    default = default_order_deductions(person, period)
    # The income left in earned taxable income before allowances, under
    # that order. The part of it above earnings is the person's other
    # non-savings income. Trade loss relief comes off that other income
    # first; net_income deducts all of it, so add back the part the order
    # sets against savings and dividends.
    income_in_base = (
        person("net_income", period)
        + default.relief_against_savings_and_dividends
        - add(person, period, excluded_incomes)
    )
    other_income = max_(0, income_in_base - earnings)
    # Earned taxable income under that order: the exclusions with the old
    # order's allowances against non-savings income in place of the share's.
    excluded = add(
        person,
        period,
        [
            variable
            for variable in exclusions
            if variable != "received_allowances_earned_income"
        ],
    )
    if "received_allowances_earned_income" in exclusions:
        excluded = excluded + default.earned
    earned_taxable = max_(
        0,
        person("net_income", period)
        + default.relief_against_savings_and_dividends
        - excluded,
    )
    taxable_earnings = max_(0, earned_taxable - other_income)
    rates = income_tax.rates
    gross_gift = person("gift_aid_grossed_up", period)
    tax = where(
        person("pays_scottish_income_tax", period),
        calc_income_tax_with_gift_aid(
            rates.scotland.rates,
            taxable_earnings,
            gross_gift,
            first_extended_scottish_threshold(rates.scotland.rates),
            len(rates.scotland.rates.thresholds),
        ),
        calc_income_tax_with_gift_aid(rates.uk, taxable_earnings, gross_gift),
    )
    # Tax reductions (for example the married couple's allowance) come
    # off the tax on earnings first, as allowances do. So the deduction
    # never exceeds the income tax the person pays, never includes a
    # charge such as the High Income Child Benefit Charge, and does not
    # move when other income absorbs more or less of a reduction. The
    # exception is the finance-cost reduction, which is given on property
    # profits and limited by them (ITTOIA 2005 s. 274AA), so it comes off
    # the tax on property income first. Only a part larger than that tax
    # (possible where Scottish rates on property income are below the
    # reduction's rate) comes off the tax on earnings.
    return max_(0, tax - earnings_tax_reductions(person, period, parameters))

import numpy as np

from policyengine_uk.utils.supplied_inputs import supplied_input


def trading_profits_before_losses(person, period, hmrc):
    """Trading profits chargeable under ITTOIA 2005 Part 2, before losses.

    Capital allowances are a trading expense (CAA 2001 s.247) and the trading
    allowance replaces expenses (ITTOIA 2005 s.783AC), so both come off.
    Losses brought forward (ITA 2007 s.83) are a Step 2 relief, which the
    model deducts from trading profits (loss_relief); they stay in here.
    """
    from policyengine_core.model_api import add

    deductions = [
        deduction
        for deduction in hmrc.income_tax.bases.taxable_self_employment_income_deductions
        if deduction != "loss_relief"
    ]
    return np.maximum(
        0, person("self_employment_income", period) - add(person, period, deductions)
    )


def relevant_uk_earnings(person, period, hmrc):
    """FA 2004 s.189(2) relevant UK earnings.

    Employment income chargeable to income tax is net taxable earnings
    (ITEPA 2003 ss.9(2) and 11): pay and employer-paid taxable SSP, SMP and
    SPP (employment_benefits), which the model holds separately from wages,
    less the allowable expenses in s.327(3). s.327(5) also lists the deductions for pension contributions
    (FA 2004 ss.188-194), but those are the relief that these earnings limit,
    so they are not taken off; the limit would otherwise depend on itself.
    Trading income is the profit chargeable under ITTOIA 2005 Part 2, before
    losses. A trading loss does not reduce employment earnings (HMRC
    PTM044100). Furnished holiday lettings profits, relevant UK earnings
    before 2025-26 (s.189(2)(ba) and (bb)), are not modelled separately.
    """
    return person("taxable_employment_income", period) + (
        trading_profits_before_losses(person, period, hmrc)
    )


def pension_contributions_relief_amount(
    contributions, relevant_uk_earnings, ras_contributions, age, hmrc
):
    """FA 2004 ss. 188–191 relief for the supplied actual pay/contributions.

    Only RAS can use the basic-amount increase above earnings (s. 191(7)).
    The annual allowance does not cap relief, and payments from age 75 are
    unrelievable. The AA income tests use the same actual-payment convention.
    """
    basic_amount_increase = np.minimum(
        np.maximum(
            0,
            hmrc.income_tax.reliefs.pension_contribution.basic_amount
            - relevant_uk_earnings,
        ),
        ras_contributions,
    )
    annual_limit = relevant_uk_earnings + basic_amount_increase
    under_age_limit = age < hmrc.pensions.pension_contributions_relief_age_limit
    return np.minimum(contributions, annual_limit) * under_age_limit


def annual_allowance_net_income(person, period, parameters):
    """Model net income with the annual-allowance net-pay/loss ordering.

    Like net_income, this is before the separately modelled pension relief.
    ITA 2007 ss.24A, 25 and 64 require recomputing the loss deduction after
    relievable net pay. A supplied legacy return is actual pay/member payment;
    the computed NICs-only excess never enters income or contributions.
    """
    hmrc = parameters(period).gov.hmrc
    actual_member_contributions = person("pension_contributions", period)
    actual_earnings = relevant_uk_earnings(person, period, hmrc)
    supplied_ani = supplied_input(person, "adjusted_net_income", period)
    if supplied_ani is not None:
        # Supplied ANI already determines net income, including its losses.
        # Restore only Gift Aid and pension relief on actual earnings/payments;
        # A replacement loss deduction does not belong on this input path.
        return (
            supplied_ani
            + person("gift_aid_grossed_up", period)
            + pension_contributions_relief_amount(
                actual_member_contributions,
                actual_earnings,
                person("personal_pension_contributions", period),
                person("age", period),
                hmrc,
            )
        )

    net_income = person("net_income", period)
    actual_net_pay = person("employee_pension_contributions", period)
    relievable_net_pay = pension_contributions_relief_amount(
        actual_net_pay, actual_earnings, 0, person("age", period), hmrc
    )
    if not np.any((relievable_net_pay > 0) & (person("trading_loss", period) > 0)):
        return net_income

    income_before_loss = np.maximum(
        0, person("net_income_before_trade_loss_relief", period)
    )
    # Rebuild adjusted_total_income (s.24A(8)) from actual pay and member
    # contributions, retaining its treatment of brought-forward trade losses
    # and pension relief. Brought-forward losses only reduce trading profits.
    losses_brought_forward_deducted = trading_profits_before_losses(
        person, period, hmrc
    ) - person("taxable_self_employment_income", period)
    relieved_contributions = pension_contributions_relief_amount(
        actual_member_contributions,
        actual_earnings,
        person("personal_pension_contributions", period),
        person("age", period),
        hmrc,
    )
    adjusted_total = np.maximum(
        0,
        income_before_loss + losses_brought_forward_deducted - relieved_contributions,
    )
    cap = hmrc.income_tax.reliefs.cap
    loss_cap = np.maximum(cap.amount, cap.rate * adjusted_total)
    loss = np.where(
        person("trading_allowance_deduction", period) > 0,
        0,
        person("trading_loss", period),
    )
    # FA 2004 s.193(2) deducts relievable net pay from employment income
    # before the s.25(4) limit on Step 2 loss relief. Apply this ordering even
    # without a NICs return, retaining the pre-pension-relief model convention
    # below so the callers can deduct or restore member relief once.
    income_after_net_pay = np.maximum(0, income_before_loss - relievable_net_pay)
    actual_loss_relief = np.minimum(loss, np.minimum(loss_cap, income_after_net_pay))
    # Replace the original loss with the loss after relievable net pay.
    # Supplied ANI has its own path above. This ordering also applies before
    # the NICs cap starts and when the actual legacy return is zero.
    reconstructed = np.maximum(
        0,
        net_income
        + person("trade_loss_relief_against_general_income", period)
        - actual_loss_relief,
    )
    return np.where(relievable_net_pay > 0, reconstructed, net_income)


def annual_allowance_for_year(adjusted_income, threshold_income, allowance, year):
    """The annual allowance (FA 2004 s.228) under one tax year's parameters.

    From 2016-17 the standard allowance is tapered only when both adjusted
    income and threshold income exceed their limits (s.228ZA), and the
    reduction rounds down to whole pounds before the tapered minimum
    applies. The original multiplier is the standard allowance less £10,000
    over £60,000, a half at the statutory £40,000; from 2020-21 the
    multiplier is expressly a half.
    """
    adjusted_income = np.asarray(adjusted_income, dtype=float)
    if year < 2016:
        return np.full(adjusted_income.shape, float(allowance.default))
    if year < 2020:
        rate = (allowance.default - allowance.minimum) / allowance.taper_income_range
    else:
        rate = allowance.reduction_rate
    # s.228ZA(3)(b) derives the threshold limit from the standard allowance.
    high_income = (adjusted_income > allowance.taper) & (
        np.asarray(threshold_income) > allowance.taper - allowance.default
    )
    reduction = np.floor(np.maximum(0, adjusted_income - allowance.taper) * rate)
    return np.where(
        high_income,
        np.maximum(allowance.minimum, allowance.default - reduction),
        allowance.default,
    )


def workplace_pension_contributions(person, period):
    """Contributions to workplace arrangements.

    Employer contributions, employee contributions under a net pay
    arrangement (including any supplied legacy return to ordinary pay, an
    actual member payment) and the full salary sacrifice. The NICs-only
    salary-sacrifice excess is not a contribution. Personal pension
    contributions (relief at source) are not included.
    """
    return (
        person("employee_pension_contributions", period)
        + person("employer_pension_contributions", period)
        + person("pension_contributions_via_salary_sacrifice_from_pay", period)
    )

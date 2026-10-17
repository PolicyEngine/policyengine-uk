import numpy as np

from policyengine_uk.utils.supplied_inputs import supplied_input


def pension_contributions_relief_amount(
    contributions, relevant_uk_earnings, ras_contributions, age, hmrc
):
    """FA 2004 ss. 188–191 relief for the supplied actual pay/contributions.

    Only RAS can use the basic-amount increase above earnings (s. 191(7)).
    The annual allowance does not cap relief, and payments from age 75 are
    unrelievable. Keeping this calculation shared lets the AA income tests
    exclude the NICs-only salary-sacrifice reclassification exactly.
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
    """Model net income rebuilt without NICs-only returned salary sacrifice.

    Like net_income, this is before the separately modelled pension relief.
    ITA 2007 ss.24A, 25 and 64 require recomputing the loss deduction, not
    subtracting returned pay after an income-dependent deduction was taken.
    Ordinary income tax keeps its existing calculation (issue #2454).
    """
    from policyengine_core.model_api import add

    returned = person("salary_sacrifice_returned_to_income", period)
    hmrc = parameters(period).gov.hmrc
    actual_member_contributions = person("pension_contributions", period) - returned
    actual_earnings = (
        person("employment_income", period)
        - returned
        + np.maximum(0, person("self_employment_income", period))
    )
    supplied_ani = supplied_input(person, "adjusted_net_income", period)
    if supplied_ani is not None:
        # Supplied ANI already determines net income, including its losses.
        # Restore only Gift Aid and pension relief on actual earnings/payments;
        # neither returned pay nor a replacement loss deduction belongs here.
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
    actual_net_pay = person("employee_pension_contributions", period) - returned
    relievable_net_pay = pension_contributions_relief_amount(
        actual_net_pay, actual_earnings, 0, person("age", period), hmrc
    )
    if not np.any(returned) and not np.any(
        (relievable_net_pay > 0) & (person("trading_loss", period) > 0)
    ):
        return net_income

    taxable_pay = person("taxable_employment_income", period)
    actual_taxable_pay = np.maximum(0, taxable_pay - returned)
    removed_taxable_pay = taxable_pay - actual_taxable_pay
    income_before_loss = np.maximum(
        0,
        person("net_income_before_trade_loss_relief", period) - removed_taxable_pay,
    )
    # Rebuild adjusted_total_income (s.24A(8)) from actual pay and member
    # contributions, retaining its treatment of brought-forward trade losses
    # and pension relief. Brought-forward losses only reduce trading profits.
    other_deductions = [
        deduction
        for deduction in hmrc.income_tax.bases.taxable_self_employment_income_deductions
        if deduction != "loss_relief"
    ]
    profits_before_carry_forward = np.maximum(
        0,
        person("self_employment_income", period)
        - add(person, period, other_deductions),
    )
    losses_brought_forward_deducted = profits_before_carry_forward - person(
        "taxable_self_employment_income", period
    )
    relief_limit = np.maximum(
        hmrc.income_tax.reliefs.pension_contribution.basic_amount,
        actual_taxable_pay + profits_before_carry_forward,
    )
    relieved_contributions = np.minimum(actual_member_contributions, relief_limit) * (
        person("age", period) < hmrc.pensions.pension_contributions_relief_age_limit
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
    # Add back the loss computed using synthetic pay before deducting the
    # actual-pay loss. Supplied ANI has its own path above. For other people,
    # net-pay/loss ordering also applies before the NICs cap starts.
    reconstructed = np.maximum(
        0,
        net_income
        + person("trade_loss_relief_against_general_income", period)
        - removed_taxable_pay
        - actual_loss_relief,
    )
    return np.where(
        (returned > 0) | (relievable_net_pay > 0), reconstructed, net_income
    )

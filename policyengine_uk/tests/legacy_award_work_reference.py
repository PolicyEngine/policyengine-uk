"""Reference readings of the income-related ESA and income-based JSA screens.

Written from the law, family by family and in plain Python, for property
tests to compare with the model (test_legacy_award_work_properties.py and
test_income_support_eligibility_properties.py). Each adult is a dict of
simulation inputs for one year: hours_worked (annual), employment_income,
self_employment_income, employee_pension_contributions,
personal_pension_contributions, statutory_sick_pay, statutory_maternity_pay,
statutory_paternity_pay, receives_carer_benefit, care_hours, age and the
reported awards.

- Capital (WRA 2007 Sch 1 para 6(1)(b), ESA Regs reg 110; JSA 1995 s.13(1),
  JSA Regs reg 107): within £16,000, with £1 a week of tariff income for
  each £250 or part over £6,000.
- ESA claimant (para 6(1)(e), ESA Regs reg 41(1)): paid work is remunerative
  unless it is exempt work: earnings of no more than £20 a week (reg 45(2)),
  or under 16 hours with earnings within the higher limit (reg 45(4)).
  Pay is net of PAYE and primary Class 1 on the pay alone and half the
  pension contributions (reg 96(3)). Statutory sick, maternity and
  paternity pay are not earnings (reg 95(2)(b)): they are ignored, and no
  tax or Class 1 on them comes off the pay. Self-employment is the profit
  less a notional basic-rate tax on the profit above the personal allowance,
  notional main-rate Class 4 (and Class 2 before 6 April 2024) and half the
  personal pension contributions (reg 98(3), reg 99); a loss is not set
  against pay (reg 98(11)).
- ESA partner (para 6(1)(f), reg 42(1)): 24 hours or more, unless a carer
  (reg 43(2)(c)).
- JSA claimant (s.1(2)(e), reg 51(1)(a)): 16 hours or more, with no
  exception for carers doing unrelated paid work. The other member of the
  couple: 24 hours or more (s.3(1)(e), reg 51(1)(b)). In a joint-claim
  couple each member is a claimant at 16 hours (s.1(2B)(b)), but a member
  may claim alone when the other works 16 to under 24 hours (reg 3E(1),
  (2)(g)), so the limit is 24 either way.
- The claimant is a member who reports the award; when the claimant or
  partner reports one, only they are candidates.
"""

import math

WEEKS = 52


def tariff_income(capital, rules):
    """Annual tariff income: £1 a week for each £250 (or part) over £6,000."""
    excess = max(0, capital - rules.tariff_income.threshold)
    return (
        math.ceil(excess / rules.tariff_income.step)
        * rules.tariff_income.amount
        * WEEKS
    )


def award_survives_capital_test(reported, capital, rules):
    """Whether a reported award survives a legacy benefit's capital test."""
    return (
        reported > 0
        and capital <= rules.limit
        and reported > tariff_income(capital, rules)
    )


def carer(adult):
    return (
        adult.get("receives_carer_benefit", False) or adult.get("care_hours", 0) >= 35
    )


def weekly_hours(adult):
    return adult.get("hours_worked", 0) / WEEKS


def esa_weekly_earnings(adult, parameters):
    """Net weekly earnings for the exempt work limits. Covers pay within the
    basic rate band, a self-employment profit within the Class 4 upper limit
    or a loss, any mix of the two, and no other income, for someone in
    England; National Insurance stops at state pension age (66 in the years
    tested)."""
    hmrc = parameters.gov.hmrc
    allowance = hmrc.income_tax.allowances.personal_allowance.amount
    basic_rate = hmrc.income_tax.rates.uk.rates[0]
    ni_liable = adult["age"] < 66
    pay = adult.get("employment_income", 0)
    profit = max(0, adult.get("self_employment_income", 0))
    employee_pension = adult.get("employee_pension_contributions", 0)
    personal_pension = adult.get("personal_pension_contributions", 0)
    pension_from_profit = personal_pension if profit > 0 else 0
    pension_from_pay = employee_pension + personal_pension - pension_from_profit
    assert pay <= hmrc.income_tax.rates.uk.thresholds[1] + allowance, adult
    # Reg 96(3): PAYE on the pay alone, with employee contributions taken off
    # taxable pay (net pay arrangements).
    tax_on_pay = basic_rate * max(0, pay - min(employee_pension, pay) - allowance)
    class_1 = hmrc.national_insurance.class_1
    threshold = class_1.thresholds.primary_threshold * WEEKS
    class_1_on_pay = (
        class_1.rates.employee.main * max(0, pay - threshold) if ni_liable else 0
    )
    net_pay = max(0, pay - tax_on_pay - class_1_on_pay - pension_from_pay / 2)
    # Reg 99(1): basic rate on the profit less the personal allowance, whatever
    # relief pension contributions attract. Reg 99(3)(b): main-rate Class 4.
    # Reg 99(3)(a): Class 2, before 6 April 2024.
    notional_tax = basic_rate * max(0, profit - allowance)
    nics = hmrc.national_insurance
    class_4 = nics.class_4
    assert profit <= class_4.thresholds.upper_profits_limit, adult
    notional_class_4 = (
        class_4.rates.main * max(0, profit - class_4.thresholds.lower_profits_limit)
        if ni_liable
        else 0
    )
    rule = parameters.gov.dwp.ESA.income.self_employment_class_2
    if rule.above_lower_profits_threshold:
        class_2_due = profit > nics.class_2.lower_profits_threshold
    else:
        class_2_due = profit >= nics.class_2.small_profits_threshold
    notional_class_2 = (
        nics.class_2.flat_rate * WEEKS
        if rule.deducted and class_2_due and ni_liable
        else 0
    )
    net_profit = max(
        0,
        profit
        - notional_tax
        - notional_class_4
        - notional_class_2
        - pension_from_profit / 2,
    )
    return (net_pay + net_profit) / WEEKS


def esa_claimant_in_remunerative_work(adult, parameters):
    exempt_work = parameters.gov.dwp.ESA.exempt_work
    earnings = esa_weekly_earnings(adult, parameters)
    within_lower_limit = earnings <= exempt_work.lower_earnings_limit
    permitted_work = (
        weekly_hours(adult) < exempt_work.hours_limit
        and earnings <= exempt_work.higher_earnings_limit
    )
    return not (within_lower_limit or permitted_work)


def candidates(couple, others, reported):
    """Indexes (into couple + others) of members who could be the claimant."""
    members = couple + others
    couple_reports = any(adult.get(reported, 0) > 0 for adult in couple)
    return [
        i
        for i, member in enumerate(members)
        if member.get(reported, 0) > 0 and (i < len(couple) or not couple_reports)
    ]


def esa_screen(couple, others, capital, parameters):
    """esa_income_eligible for a claimant and partner (couple) and other
    members of the benefit unit outside the family (others)."""
    ESA = parameters.gov.dwp.ESA.income
    members = couple + others

    def other_member_works(i):
        if i >= len(couple):
            return False
        return any(
            not carer(other)
            and weekly_hours(other) >= ESA.remunerative_work.partner_hours
            for j, other in enumerate(couple)
            if j != i
        )

    passes = any(
        not esa_claimant_in_remunerative_work(members[i], parameters)
        and not other_member_works(i)
        for i in candidates(couple, others, "esa_income_reported")
    )
    return passes and capital <= ESA.capital.limit


def jsa_screen(couple, others, capital, parameters):
    """jsa_income_eligible for a claimant and partner (couple) and other
    members of the benefit unit outside the family (others)."""
    JSA = parameters.gov.dwp.JSA
    WORK = JSA.remunerative_work
    members = couple + others
    other_limit = WORK.partner_hours

    def other_member_works(i):
        if i >= len(couple):
            return False
        return any(
            weekly_hours(other) >= other_limit
            for j, other in enumerate(couple)
            if j != i
        )

    passes = any(
        weekly_hours(members[i]) < WORK.claimant_hours and not other_member_works(i)
        for i in candidates(couple, others, "jsa_income_reported")
    )
    return passes and capital <= JSA.income.capital.limit

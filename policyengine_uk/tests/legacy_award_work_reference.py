"""Reference readings of the income-related ESA and income-based JSA screens.

Written from the law, family by family and in plain Python, for property
tests to compare with the model (test_legacy_award_work_properties.py and
test_income_support_eligibility_properties.py). Each adult is a dict of
simulation inputs for one year: hours_worked (annual), employment_income,
employee_pension_contributions, receives_carer_benefit, care_hours, age and
the reported awards.

- Capital (WRA 2007 Sch 1 para 6(1)(b), ESA Regs reg 110; JSA 1995 s.13(1),
  JSA Regs reg 107): within £16,000, with £1 a week of tariff income for
  each £250 or part over £6,000.
- ESA claimant (para 6(1)(e), ESA Regs reg 41(1)): paid work is remunerative
  unless it is exempt work: earnings of no more than £20 a week (reg 45(2)),
  or under 16 hours with earnings within the higher limit (reg 45(4)).
  Earnings are net of income tax, National Insurance and half the pension
  contributions (regs 96(3), 98(4)).
- ESA partner (para 6(1)(f), reg 42(1)): 24 hours or more, unless a carer
  (reg 43(2)(c)).
- JSA claimant (s.1(2)(e), reg 51(1)(a)): 16 hours or more, with no carer
  exception. Each member of a joint-claim couple is a claimant (s.1(2B)(b));
  otherwise the partner's limit is 24 hours (s.3(1)(e), reg 51(1)(b)).
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
    """Net weekly earnings for the exempt work limits, for an employee with no
    other income and earnings within the basic rate band."""
    gross = adult.get("employment_income", 0)
    pension = adult.get("employee_pension_contributions", 0)
    hmrc = parameters.gov.hmrc
    allowance = hmrc.income_tax.allowances.personal_allowance.amount
    basic_rate = hmrc.income_tax.rates.uk.rates[0]
    # Pension contributions are only used with pay below the personal
    # allowance, so how they are relieved for tax does not arise.
    assert pension == 0 or gross <= allowance, adult
    tax = basic_rate * max(0, gross - allowance)
    class_1 = hmrc.national_insurance.class_1
    threshold = class_1.thresholds.primary_threshold * WEEKS
    national_insurance = class_1.rates.employee.main * max(0, gross - threshold)
    return max(0, gross - tax - national_insurance - pension / 2) / WEEKS


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


def jsa_joint_claim(couple, family_has_child, year, parameters):
    joint_claim = parameters.gov.dwp.JSA.income.joint_claim
    return (
        bool(joint_claim.in_effect)
        and len(couple) == 2
        and not family_has_child
        and any(
            adult["age"] >= 18 and year - adult["age"] > joint_claim.born_after_year
            for adult in couple
        )
    )


def jsa_screen(couple, others, capital, joint_claim, parameters):
    """jsa_income_eligible for a claimant and partner (couple), other members
    of the benefit unit outside the family (others) and the couple's
    joint-claim status."""
    JSA = parameters.gov.dwp.JSA
    WORK = JSA.remunerative_work
    members = couple + others
    other_limit = WORK.claimant_hours if joint_claim else WORK.partner_hours

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

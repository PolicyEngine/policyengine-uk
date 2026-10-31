"""The income on which student loan repayments and interest are worked out."""

from policyengine_core.model_api import max_, min_


def student_loan_income(person, period):
    """Net income less the benefits in kind it holds.

    Benefits in kind are not repayment income: Self Assessment leaves out
    the car benefits of ITEPA 2003 Part 3 Chapter 6 (SI 2009/470 reg.
    29(4)(e)), and PAYE deducts repayments from Class 1 earnings only
    (reg. 41). Plan 2 interest income is the same income (reg. 21A(11)).

    Allowable deductions come off pay and benefits together (ITEPA 2003
    s. 11), so where they exceed pay, taxable employment income holds only
    part of the benefits. Taxable employment income is the pay and benefits
    less deductions, floored at zero, so it holds the smaller of itself and
    the benefits: only that much comes off.
    """
    benefits_in_net_income = min_(
        person("taxable_employment_income", period),
        person("benefits_in_kind", period),
    )
    return max_(person("net_income", period) - benefits_in_net_income, 0)

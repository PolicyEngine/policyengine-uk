from policyengine_uk.model_api import *


class uc_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit earned income (after deductions and work allowance)"
    documentation = (
        "The claimant's earned income, or joint claimants' combined earned "
        "income, less the work allowance. Earnings of a child, a qualifying "
        "young person or anyone else in the benefit unit who is not a "
        "claimant do not count."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 22(1)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/22",
        ),
        dict(
            title="Welfare Reform Act 2012 s. 8(3) and (4)",
            href="https://www.legislation.gov.uk/ukpga/2012/5/section/8",
        ),
    ]

    def formula(benunit, period, parameters):
        # Reg. 22(1)(b) deducts "the claimant's earned income (or, in the case
        # of joint claimants, their combined earned income)". Each claimant's
        # earned income is net of their own deductions (reg. 55(5), reg.
        # 57(2)), summed over the claimants
        # (uc_earned_income_before_work_allowance); the work allowance then
        # comes off the combined earned income before the taper.
        earned_income = benunit("uc_earned_income_before_work_allowance", period)
        work_allowance = benunit("uc_work_allowance", period)
        return max_(0, earned_income - work_allowance)

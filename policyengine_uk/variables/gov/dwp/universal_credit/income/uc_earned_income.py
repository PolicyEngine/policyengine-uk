from policyengine_uk.model_api import *


class uc_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit earned income (after deductions and work allowance)"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Universal Credit Regulations 2013 reg. 22(1)(b)",
        href="https://www.legislation.gov.uk/uksi/2013/376/regulation/22",
    )

    def formula(benunit, period, parameters):
        # Each person's earned income is net of their own deductions
        # (reg. 55(5), reg. 57(2)); the work allowance then comes off the
        # combined earned income before the taper (reg. 22(1)(b)).
        earned_income = benunit("uc_earned_income_before_work_allowance", period)
        work_allowance = benunit("uc_work_allowance", period)
        return max_(0, earned_income - work_allowance)

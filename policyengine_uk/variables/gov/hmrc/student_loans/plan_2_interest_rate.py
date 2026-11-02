from policyengine_uk.model_api import *
from policyengine_uk.utils.student_loans import student_loan_income
import numpy as np


class plan_2_interest_rate(Variable):
    value_type = float
    entity = Person
    label = "Plan 2 student loan interest rate"
    documentation = (
        "Income-contingent interest rate for Plan 2 student loans. "
        "RPI only below lower threshold, tapered to RPI+3% at upper threshold. "
        "Note: Actual rates are set annually in September using March RPI."
    )
    definition_period = YEAR
    unit = "/1"
    reference = "https://www.legislation.gov.uk/uksi/2012/1309/regulation/10"

    def formula(person, period, parameters):
        # Interest income is the repayment income (SI 2009/470 reg. 21A(11)),
        # which leaves out benefits in kind (regs. 29(4)(e) and 41).
        income = student_loan_income(person, period)
        p = parameters(period).gov.hmrc.student_loans
        rpi = parameters(period).gov.economic_assumptions.yoy_growth.obr.rpi

        # Per Regulation 21AB, lower interest threshold = repayment threshold
        # Below lower: RPI only; above upper: RPI + 3%; between: linear taper
        taper_fraction = np.clip(
            (income - p.thresholds.plan_2)
            / (p.interest_rates.plan_2.upper_threshold - p.thresholds.plan_2),
            0,
            1,
        )
        return rpi + p.interest_rates.plan_2.additional_rate * taper_fraction

from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.hmrc.student_loans.student_loan_plan import (
    StudentLoanPlan,
)
import numpy as np


class student_loan_repayment(Variable):
    value_type = float
    entity = Person
    label = "Student loan repayment (modelled)"
    documentation = (
        "Annual student loan repayment calculated from income and plan type. "
        "Repayments are 9% of income above the plan-specific threshold."
    )
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        plan = person("student_loan_plan", period)
        income = person("adjusted_net_income", period)
        rate = parameters(period).gov.hmrc.student_loans.repayment_rate
        thresholds = parameters(period).gov.hmrc.student_loans.thresholds

        # Get threshold based on plan type
        threshold = select(
            [
                plan == StudentLoanPlan.PLAN_1,
                plan == StudentLoanPlan.PLAN_2,
                plan == StudentLoanPlan.PLAN_4,
                plan == StudentLoanPlan.PLAN_5,
            ],
            [
                thresholds.plan_1,
                thresholds.plan_2,
                thresholds.plan_4,
                thresholds.plan_5,
            ],
            default=np.inf,
        )

        repayment = rate * max_(0, income - threshold)
        return repayment


class has_student_loan(Variable):
    value_type = bool
    entity = Person
    label = "Has student loan"
    documentation = "Whether the person has a student loan."
    definition_period = YEAR

    def formula(person, period, parameters):
        plan = person("student_loan_plan", period)
        return plan != StudentLoanPlan.NONE

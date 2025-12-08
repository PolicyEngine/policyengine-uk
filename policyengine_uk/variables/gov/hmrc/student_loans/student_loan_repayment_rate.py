from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.hmrc.student_loans.student_loan_plan import (
    StudentLoanPlan,
)


class student_loan_repayment_rate(Variable):
    value_type = float
    entity = Person
    label = "Student loan repayment rate"
    documentation = (
        "Percentage of income above threshold paid toward student loan. "
        "9% for Plans 1/2/4/5, 6% for Postgraduate loans."
    )
    definition_period = YEAR
    unit = "/1"
    reference = "https://www.gov.uk/repaying-your-student-loan/what-you-pay"

    def formula(person, period, parameters):
        plan = person("student_loan_plan", period)
        p = parameters(period).gov.hmrc.student_loans

        return where(
            plan == StudentLoanPlan.POSTGRADUATE,
            p.postgraduate_repayment_rate,
            where(
                plan == StudentLoanPlan.NONE,
                0,
                p.repayment_rate,
            ),
        )

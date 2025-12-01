from policyengine_uk.model_api import *


class StudentLoanPlan(Enum):
    NONE = "NONE"
    PLAN_1 = "PLAN_1"
    PLAN_2 = "PLAN_2"
    PLAN_4 = "PLAN_4"
    PLAN_5 = "PLAN_5"
    POSTGRADUATE = "POSTGRADUATE"


class student_loan_plan(Variable):
    value_type = Enum
    possible_values = StudentLoanPlan
    default_value = StudentLoanPlan.NONE
    entity = Person
    label = "Student loan plan type"
    documentation = (
        "The type of student loan plan the person is on. "
        "Plan 1: Started before Sept 2012 (England/Wales) or any time (NI). "
        "Plan 2: Started Sept 2012 - Aug 2023 (England/Wales). "
        "Plan 4: Scotland. "
        "Plan 5: Started Aug 2023 onwards (England). "
        "Postgraduate: Master's or Doctoral loans."
    )
    definition_period = YEAR

from policyengine_uk.model_api import *


class student_loan_balance(Variable):
    value_type = float
    entity = Person
    label = "Student loan balance"
    documentation = (
        "Outstanding student loan balance. "
        "When not provided, repayments are left uncapped."
    )
    definition_period = YEAR
    unit = GBP
    default_value = 0

from policyengine_uk.model_api import *


class student_loan_repayments(Variable):
    label = "student loan repayments"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        return person("student_loan_repayment", period)

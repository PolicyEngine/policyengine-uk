from policyengine_uk.model_api import *


class student_loan_repayments(Variable):
    label = "student loan repayments"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.average_earnings"

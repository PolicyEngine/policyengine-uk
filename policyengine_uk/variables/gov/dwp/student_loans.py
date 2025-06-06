from policyengine_uk.model_api import *


class student_loans(Variable):
    value_type = float
    entity = Person
    label = "Student loans"
    definition_period = YEAR
    unit = GBP

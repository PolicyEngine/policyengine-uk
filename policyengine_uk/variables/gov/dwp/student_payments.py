from policyengine_uk.model_api import *


class student_payments(Variable):
    value_type = float
    entity = Person
    label = "Student payments"
    definition_period = YEAR
    unit = GBP

    adds = ["adult_ema", "child_ema", "access_fund", "education_grants"]

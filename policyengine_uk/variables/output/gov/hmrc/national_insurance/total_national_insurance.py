from policyengine_uk.model_api import *


class total_national_insurance(Variable):
    label = "total National Insurance"
    documentation = "Employee, employer and self-employed NI contributions."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "national_insurance",
        "ni_class_1_employer",
    ]

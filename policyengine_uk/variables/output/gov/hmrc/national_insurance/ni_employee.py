from policyengine_uk.model_api import *


class ni_employee(Variable):
    value_type = float
    entity = Person
    label = "employee-side National Insurance"
    definition_period = YEAR
    unit = GBP
    adds = [
        "ni_class_1_employee",
    ]

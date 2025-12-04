from policyengine_uk.model_api import *


class national_insurance(Variable):
    value_type = float
    entity = Person
    label = "National Insurance"
    documentation = "Total National Insurance contributions"
    definition_period = YEAR
    unit = GBP
    reference = "Social Security and Benefits Act 1992 s. 1(2)"
    adds = [
        "ni_class_1_employee",
        "ni_class_2",
        "ni_class_3",
        "ni_class_4",
    ]

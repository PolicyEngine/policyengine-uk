from policyengine_uk.model_api import *


class ni_class_1_employee(Variable):
    label = "NI Class 1 employee-side contributions"
    entity = Person
    definition_period = MONTH
    value_type = float
    unit = GBP
    defined_for = "ni_liable"
    adds = [
        "ni_class_1_employee_primary",
        "ni_class_1_employee_additional",
    ]
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/8"

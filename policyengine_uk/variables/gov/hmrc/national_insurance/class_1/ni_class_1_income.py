from policyengine_uk.model_api import *


class ni_class_1_income(Variable):
    label = "ni_class_1_income"
    documentation = "Income subject to NI Class 1 contributions."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "employment_income",
        "statutory_sick_pay",
        "statutory_maternity_pay",
        "statutory_paternity_pay",
    ]
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/3"

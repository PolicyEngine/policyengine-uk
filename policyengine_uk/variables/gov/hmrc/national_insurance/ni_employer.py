from policyengine_uk.model_api import *


class ni_employer(Variable):
    value_type = float
    entity = Person
    label = "employer-side National Insurance"
    definition_period = YEAR
    unit = GBP
    adds = [
        "ni_class_1_employer",
    ]

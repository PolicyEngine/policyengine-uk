from policyengine_uk.model_api import *


class ni_self_employed(Variable):
    value_type = float
    entity = Person
    label = "self-employed National Insurance"
    definition_period = YEAR
    unit = GBP
    adds = [
        "ni_class_2",
        "ni_class_4",
    ]

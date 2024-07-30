from policyengine_uk.model_api import *


class education_consumption(Variable):
    label = "education consumption"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW
    adds = [
        "private_school_fees",
        "non_private_school_education_consumption",
    ]

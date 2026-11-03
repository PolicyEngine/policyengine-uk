from policyengine_uk.model_api import *


class ni_employer(Variable):
    value_type = float
    entity = Person
    label = "employer-side National Insurance"
    documentation = (
        "Secondary Class 1 contributions on the person's earnings and Class "
        "1A contributions on their benefits in kind."
    )
    definition_period = YEAR
    unit = GBP
    adds = [
        "ni_class_1_employer",
        "ni_class_1a",
    ]

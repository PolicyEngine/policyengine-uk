from policyengine_uk.model_api import *


class non_private_school_education_consumption(Variable):
    label = "non-private school education consumption"
    documentation = "Education spending not on private school fees."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


from policyengine_uk.model_api import *


class private_school_fees(Variable):
    label = "private school fees"
    documentation = "Private school fees paid in respect of this person."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


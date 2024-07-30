from policyengine_uk.model_api import *


class alcohol_and_tobacco_consumption(Variable):
    label = "alcohol and tobacco consumption"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

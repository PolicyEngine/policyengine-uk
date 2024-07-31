from policyengine_uk.model_api import *


class state_pension(Variable):
    label = "State Pension"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

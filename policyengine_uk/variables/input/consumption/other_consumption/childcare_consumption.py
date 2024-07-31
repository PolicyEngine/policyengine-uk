from policyengine_uk.model_api import *


class childcare_consumption(Variable):
    label = "childcare consumption"
    documentation = "Consumption on childcare for this person."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW

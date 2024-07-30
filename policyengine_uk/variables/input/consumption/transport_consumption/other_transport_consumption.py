from policyengine_uk.model_api import *

class other_transport_consumption(Variable):
    label = "other transport consumption"
    documentation = "Transport spending excluding petrol and diesel spending."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_property_occupied(Variable):
    value_type = bool
    entity = Firm
    label = "Firm's property is occupied"
    documentation = "Whether the firm's property is occupied throughout the year. If not, it is treated as unoccupied throughout the year for business rates, and gets the empty property exemption but no other relief."
    definition_period = YEAR
    hidden_input = True
    default_value = True

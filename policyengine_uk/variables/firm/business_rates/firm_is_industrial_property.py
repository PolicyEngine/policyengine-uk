from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_is_industrial_property(Variable):
    value_type = bool
    entity = Firm
    label = "Firm's property is a qualifying industrial property"
    documentation = "Whether the firm's property is a qualifying industrial hereditament, which gets a longer empty property rates exemption in England."
    definition_period = YEAR
    hidden_input = True
    default_value = False

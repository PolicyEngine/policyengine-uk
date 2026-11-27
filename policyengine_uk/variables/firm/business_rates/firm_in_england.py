from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_in_england(Variable):
    value_type = bool
    entity = Firm
    label = "Firm's property is in England"
    documentation = "Whether the firm's property is in England. A firm_region of Wales, Scotland or Northern Ireland overrides it: Welsh and Scottish rates follow their own rules, and Northern Ireland rates are not modelled (0)."
    definition_period = YEAR
    hidden_input = True
    default_value = True

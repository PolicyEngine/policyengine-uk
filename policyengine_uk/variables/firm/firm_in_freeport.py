from policyengine_uk.model_api import *


class firm_in_freeport(Variable):
    value_type = bool
    entity = Firm
    label = "Firm operates in a freeport"
    documentation = "Whether the firm's employees work in a freeport or investment zone tax site, for the employer National Insurance zero rate."
    definition_period = YEAR
    hidden_input = True
    default_value = False

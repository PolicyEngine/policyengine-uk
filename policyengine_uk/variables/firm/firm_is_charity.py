from policyengine_uk.model_api import *


class firm_is_charity(Variable):
    value_type = bool
    entity = Firm
    label = "Firm is a charity"
    documentation = "Whether the firm is a registered charity."
    definition_period = YEAR
    hidden_input = True
    default_value = False

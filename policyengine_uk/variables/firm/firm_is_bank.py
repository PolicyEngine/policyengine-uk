from policyengine_uk.model_api import *


class firm_is_bank(Variable):
    value_type = bool
    entity = Firm
    label = "Firm is a bank"
    documentation = "Whether the firm is a bank or a member of a banking group for corporation tax purposes, including the bank surcharge."
    definition_period = YEAR
    default_value = False

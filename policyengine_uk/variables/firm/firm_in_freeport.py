from policyengine_uk.model_api import *


class firm_in_freeport(Variable):
    value_type = bool
    entity = Firm
    label = "Firm operates in a freeport"
    documentation = (
        "Whether the firm's employees work in a freeport or investment zone "
        "tax site. No rule reads it yet: the employer National Insurance zero "
        "rate for those employees enters through "
        "firm_zero_rated_class_1_earnings, and freeport capital allowances "
        "and business rates relief are not modelled."
    )
    definition_period = YEAR
    hidden_input = True
    default_value = False

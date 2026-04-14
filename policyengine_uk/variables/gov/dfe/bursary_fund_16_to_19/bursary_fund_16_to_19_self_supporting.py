from policyengine_uk.model_api import *


class bursary_fund_16_to_19_self_supporting(Variable):
    value_type = bool
    entity = Person
    label = "Self-supporting for 16 to 19 Bursary Fund"
    documentation = (
        "Whether the student is financially supporting themselves, or themselves and a dependent living with them, "
        "for 16 to 19 Bursary Fund purposes."
    )
    definition_period = YEAR
    default_value = False
    set_input = set_input_dispatch_by_period

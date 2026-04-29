from policyengine_uk.model_api import *


class childcare_grant_full_time_student(Variable):
    value_type = bool
    entity = Person
    label = "Full-time student for Childcare Grant"
    documentation = (
        "Whether the person is studying full-time for Childcare Grant purposes. "
        "This must currently be set explicitly in simulations because the core model "
        "does not yet expose a reliable full-time higher-education status proxy."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period
    default_value = False

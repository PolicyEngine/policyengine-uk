from policyengine_uk.model_api import *


class childcare_grant_provider_is_nanny(Variable):
    value_type = bool
    entity = Person
    label = "Childcare provider is a nanny for Childcare Grant"
    documentation = (
        "Whether the childcare provider is a nanny for Childcare Grant purposes. "
        "This can be set explicitly in simulations and is used to enforce the "
        "2026-27 onward exclusion of nanny-provided care."
    )
    definition_period = YEAR
    default_value = False
    set_input = set_input_dispatch_by_period

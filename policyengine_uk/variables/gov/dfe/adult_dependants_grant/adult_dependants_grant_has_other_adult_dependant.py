from policyengine_uk.model_api import *


class adult_dependants_grant_has_other_adult_dependant(Variable):
    value_type = bool
    entity = Person
    label = "Has a non-partner adult dependant for Adult Dependants' Grant"
    documentation = (
        "Whether the student has a non-partner adult dependant for Adult Dependants' Grant purposes. "
        "This currently has to be set explicitly in simulations because the core model does not expose "
        "a reliable non-partner dependant-adult proxy."
    )
    definition_period = YEAR
    default_value = False
    set_input = set_input_dispatch_by_period

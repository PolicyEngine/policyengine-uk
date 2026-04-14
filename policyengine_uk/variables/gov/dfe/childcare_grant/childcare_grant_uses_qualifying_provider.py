from policyengine_uk.model_api import *


class childcare_grant_uses_qualifying_provider(Variable):
    value_type = bool
    entity = Person
    label = "Uses a qualifying childcare provider for Childcare Grant"
    documentation = (
        "Whether the student's childcare provider satisfies Childcare Grant rules. "
        "This can be set explicitly in simulations and should be set false where care is provided by a nanny "
        "from academic year 2026 to 2027 onward."
    )
    definition_period = YEAR
    default_value = True
    set_input = set_input_dispatch_by_period

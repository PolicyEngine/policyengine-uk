from policyengine_uk.model_api import *


class childcare_grant_uses_qualifying_provider(Variable):
    value_type = bool
    entity = Person
    label = "Uses a qualifying childcare provider for Childcare Grant"
    documentation = (
        "Whether the student's childcare provider satisfies Childcare Grant rules. "
        "This can be set explicitly in simulations. By default the model excludes "
        "nanny-provided care from 2026 onward."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        provider_is_nanny = person("childcare_grant_provider_is_nanny", period)
        nanny_disallowed = period.start.year >= 2026
        return ~(nanny_disallowed & provider_is_nanny)

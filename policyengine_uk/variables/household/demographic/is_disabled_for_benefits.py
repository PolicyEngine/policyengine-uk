from policyengine_uk.model_api import *


class is_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Has a disability"
    documentation = "Whether this person is disabled for benefits purposes"
    definition_period = YEAR
    reference = "Child Tax Credit Regulations 2002 s. 8"

    def formula(person, period, parameters):
        QUALIFYING_BENEFITS = [
            "dla",
            "pip",
        ]
        return add(person, period, QUALIFYING_BENEFITS) > 0

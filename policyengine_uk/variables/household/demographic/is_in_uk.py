from policyengine_uk.model_api import *


class is_in_uk(Variable):
    label = "Ordinarily resident in the UK"
    documentation = (
        "Whether the person is ordinarily resident in the United Kingdom"
    )
    entity = Person
    definition_period = YEAR
    value_type = bool
    default_value = True

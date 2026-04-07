from policyengine_uk.model_api import *


class tax_free_childcare_uses_qualifying_provider(Variable):
    label = "Tax-Free Childcare uses a qualifying childcare provider"
    documentation = (
        "Whether this person's childcare expenses are paid to a qualifying "
        "childcare provider for Tax-Free Childcare purposes."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool
    default_value = True

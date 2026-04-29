from policyengine_uk.model_api import *


class childcare_grant_receives_nhs_childcare_support(Variable):
    value_type = bool
    entity = Person
    label = "Receives NHS childcare support for Childcare Grant purposes"
    documentation = (
        "Whether the person or their partner receives childcare-cost support from the NHS, "
        "which makes them ineligible for Childcare Grant."
    )
    definition_period = YEAR
    default_value = False
    set_input = set_input_dispatch_by_period

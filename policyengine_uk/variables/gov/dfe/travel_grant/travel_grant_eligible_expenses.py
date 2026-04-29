from policyengine_uk.model_api import *


class travel_grant_eligible_expenses(Variable):
    value_type = float
    entity = Person
    label = "Eligible expenses for Travel Grant"
    documentation = (
        "Eligible travel, visa, insurance, and related Travel Grant expenses. "
        "This must be set explicitly in simulations."
    )
    definition_period = YEAR
    unit = GBP
    default_value = 0
    set_input = set_input_dispatch_by_period

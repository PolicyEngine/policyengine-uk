from policyengine_uk.model_api import *


class travel_grant_abroad_placement(Variable):
    value_type = bool
    entity = Person
    label = "Has an eligible study or work placement abroad for Travel Grant"
    documentation = (
        "Whether the student is on an eligible overseas study or work placement for Travel Grant purposes. "
        "This must be set explicitly in simulations."
    )
    definition_period = YEAR
    default_value = False
    set_input = set_input_dispatch_by_period

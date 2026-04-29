from policyengine_uk.model_api import *


class travel_grant_clinical_placement(Variable):
    value_type = bool
    entity = Person
    label = "Has an eligible UK clinical placement for Travel Grant"
    documentation = (
        "Whether the student is on an essential medical or dental clinical placement in the UK for Travel Grant purposes. "
        "This must be set explicitly in simulations."
    )
    definition_period = YEAR
    default_value = False
    set_input = set_input_dispatch_by_period

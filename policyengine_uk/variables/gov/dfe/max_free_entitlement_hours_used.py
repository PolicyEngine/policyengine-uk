from policyengine_uk.model_api import *


class max_free_entitlement_hours_used(Variable):
    value_type = float
    entity = Person
    label = "maximum hours of free childcare entitlement used"
    documentation = "The maximum weekly hours of free childcare entitlement used by the person"
    definition_period = YEAR
    default_value = 30

from policyengine_uk.model_api import *


class uc_is_in_startup_period(Variable):
    value_type = bool
    entity = Person
    label = "In a start-up period for the Universal Credit"
    documentation = (
        "Whether this person is in a 'start-up' period for Universal Credit"
    )
    definition_period = YEAR
    default_value = False

from policyengine_uk.model_api import *


class uc_is_in_startup_period(Variable):
    value_type = bool
    entity = Person
    label = "In a start-up period for the Universal Credit"
    documentation = (
        "Whether this person is in a start-up period for Universal Credit, in "
        "which the minimum income floor does not apply: an input from the "
        "data or the household, for any route into a start-up period. The "
        "model adds the start-up period of a responsible carer entering the "
        "all work-related requirements group "
        "(uc_is_in_startup_period_on_entering_all_requirements_group)."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/63"
    definition_period = YEAR
    default_value = False

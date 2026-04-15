from policyengine_uk.model_api import *


class disabled_students_allowance_receives_equivalent_support(Variable):
    value_type = bool
    entity = Person
    label = "Receives equivalent support that excludes Disabled Students' Allowance"
    documentation = (
        "Whether the person receives equivalent disability-related study support "
        "from another funding source, such as an NHS Disabled Students' Allowance "
        "or social work bursary, and is therefore excluded from Student Finance "
        "England Disabled Students' Allowance."
    )
    definition_period = YEAR
    default_value = False
    set_input = set_input_dispatch_by_period

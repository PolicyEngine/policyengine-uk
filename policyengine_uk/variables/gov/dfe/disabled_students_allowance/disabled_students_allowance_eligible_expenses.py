from policyengine_uk.model_api import *


class disabled_students_allowance_eligible_expenses(Variable):
    value_type = float
    entity = Person
    label = "Eligible Disabled Students' Allowance expenses"
    documentation = (
        "Annual study-related disability support costs that Disabled Students' "
        "Allowance can reimburse. This should exclude ordinary student costs, any "
        "support already provided by another funding source, and any personal "
        "computer contribution the student must pay themselves."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    default_value = 0
    set_input = set_input_dispatch_by_period

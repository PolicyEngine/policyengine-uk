from policyengine_uk.model_api import *


class uc_maximum_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "maximum Universal Credit amount"
    documentation = (
        "This is your total entitlement, before reduction due to income."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "is_uc_eligible"

    adds = [
        "uc_standard_allowance",
        "uc_child_element",
        "uc_disability_elements",
        "uc_carer_element",
        "uc_housing_costs_element",
        "uc_childcare_element",
    ]

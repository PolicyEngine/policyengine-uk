from policyengine_uk.model_api import *


class is_child_receiving_tax_free_childcare(Variable):
    value_type = bool
    entity = Person
    label = (
        "child is eligible for tax-free childcare based on age and entitlement"
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        # Check if child meets the age condition
        meets_age_condition = person(
            "tax_free_childcare_child_age_eligible", period
        )

        # Check if tax-free childcare contribution is greater than 0
        tfc_amount = person("tax_free_childcare", period)

        # Child is eligible if:
        # 1. Meets the age condition AND
        # 2. Tax-free childcare amount > 0
        return meets_age_condition & (tfc_amount > 0)

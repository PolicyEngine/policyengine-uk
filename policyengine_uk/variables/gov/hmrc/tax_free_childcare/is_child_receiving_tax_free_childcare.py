from policyengine_uk.model_api import *


class is_child_receiving_tax_free_childcare(Variable):
    value_type = bool
    entity = Person
    label = "child is eligible for tax-free childcare based on age and entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        # Check if child is qualifying for tax-free childcare
        is_qualifying_child = person("tax_free_childcare_qualifying_child", period)

        # Check if tax-free childcare contribution is greater than 0
        tfc_amount = person("tax_free_childcare", period)

        # Child is eligible if:
        # 1. Child is qualifying AND
        # 2. Tax-free childcare amount > 0
        return is_qualifying_child & (tfc_amount > 0)

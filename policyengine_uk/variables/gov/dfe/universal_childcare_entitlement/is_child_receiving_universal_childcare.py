from policyengine_uk.model_api import *


class is_child_receiving_universal_childcare(Variable):
    value_type = bool
    entity = Person
    label = "child is eligible for universal childcare entitlement based on age and entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        # Get child's age
        age = person("age", period)

        # Get the parameters for universal childcare entitlement
        p = parameters(period).gov.dfe.universal_childcare_entitlement

        # Check if age is within eligible range
        meets_age_condition = (age >= p.min_age) & (age < p.max_age)

        # Get the universal childcare entitlement amount
        entitlement_amount = person("universal_childcare_entitlement", period)

        # Child is eligible if:
        # 1. Age meets the condition AND
        # 2. Universal childcare entitlement amount > 0
        return meets_age_condition & (entitlement_amount > 0)

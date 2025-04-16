from policyengine_uk.model_api import *


class is_child_receiving_targeted_childcare(Variable):
    value_type = bool
    entity = Person
    label = "child is eligible for targeted childcare entitlement based on age and entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        # Get child's age
        age = person("age", period)

        # Get the parameters for targeted childcare entitlement age eligibility
        p = parameters(period).gov.dfe.targeted_childcare_entitlement

        # Check if age is eligible
        age_eligible = p.age_eligibility.calc(age)

        # Get the targeted childcare entitlement amount
        entitlement_amount = person("targeted_childcare_entitlement", period)

        # Child is eligible if:
        # 1. Age is eligible AND
        # 2. Targeted childcare entitlement amount > 0
        return age_eligible & (entitlement_amount > 0)

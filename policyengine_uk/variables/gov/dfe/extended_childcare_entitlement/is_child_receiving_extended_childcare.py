from policyengine_uk.model_api import *


class is_child_receiving_extended_childcare(Variable):
    value_type = bool
    entity = Person
    label = "child is eligible for extended childcare entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        # Get child's age
        age = person("age", period)

        # Get the parameters for extended childcare entitlement hours by age
        p = parameters(period).gov.dfe.extended_childcare_entitlement

        # Check if hours > 0 for this age (using the hours parameter)
        hours_by_age = p.hours.calc(age)

        # Get the benefit unit's extended childcare entitlement amount
        benunit = person.benunit
        entitlement_amount = benunit("extended_childcare_entitlement", period)

        # Child is eligible if:
        # 1. Hours > 0 for this age AND
        # 2. Benefit unit's entitlement amount > 0
        return (hours_by_age > 0) & (entitlement_amount > 0)

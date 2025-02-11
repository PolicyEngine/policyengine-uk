from policyengine_uk.model_api import *


class universal_childcare_entitlement_hours(Variable):
    value_type = float
    entity = Person
    label = "Universal childcare entitlement hours per year"
    documentation = "Number of free childcare hours per year each child is entitled to based on their age"
    definition_period = YEAR
    unit = "hour"

    def formula(person, period, parameters):
        # Get parameters with the correct path
        p = parameters(period).gov.dwp.universal_childcare_entitlement

        # Calculate hours based on age using the brackets structure
        age = person("age", period)
        hours_per_child = p.hours_based_on_age.calc(age)

        return hours_per_child

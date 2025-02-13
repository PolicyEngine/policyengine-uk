from policyengine_uk.model_api import *


class universal_childcare_entitlement_hours(Variable):
    value_type = float
    entity = Person
    label = "universal childcare entitlement hours per year"
    definition_period = YEAR
    unit = "hour"

    def formula(person, period, parameters):
        # Get parameters with the correct path
        p = parameters(period).gov.dwp.universal_childcare_entitlement

        # Calculate hours based on age using the brackets structure
        age = person("age", period)
        return p.hours.calc(age)

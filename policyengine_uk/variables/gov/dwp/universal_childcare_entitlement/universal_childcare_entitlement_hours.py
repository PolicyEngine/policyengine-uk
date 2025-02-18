from policyengine_uk.model_api import *


class universal_childcare_entitlement_hours(Variable):
    value_type = float
    entity = Person
    label = "universal childcare entitlement hours per year"
    definition_period = YEAR
    unit = "hour"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_childcare_entitlement
        is_eligible = person(
            "universal_childcare_entitlement_eligible", period
        )
        return where(is_eligible, p.hours, 0)

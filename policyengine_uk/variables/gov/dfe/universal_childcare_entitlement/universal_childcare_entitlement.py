from policyengine_uk.model_api import *


class universal_childcare_entitlement(Variable):
    value_type = float
    entity = Person
    defined_for = "universal_childcare_entitlement_eligible"
    label = "universal childcare entitlement amount per year"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe
        age = person("age", period)
        hours = p.universal_childcare_entitlement.hours
        max_hours_used = person("max_free_entitlement_hours_used", period)
        weeks = p.weeks_per_year
        total_hours_used = max_hours_used * weeks

        hours_to_use = min_(total_hours_used, hours)
        return hours_to_use * p.childcare_funding_rate.calc(age)

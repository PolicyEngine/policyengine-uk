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
        return hours * p.childcare_funding_rate.calc(age)

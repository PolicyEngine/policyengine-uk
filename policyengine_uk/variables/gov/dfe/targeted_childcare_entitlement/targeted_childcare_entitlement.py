from policyengine_uk.model_api import *


class targeted_childcare_entitlement(Variable):
    value_type = float
    entity = Person
    label = "targeted childcare entitlement amount"
    definition_period = YEAR
    unit = GBP
    defined_for = "targeted_childcare_entitlement_eligible"

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe
        age = person("age", period)
        hours = p.targeted_childcare_entitlement.hours.calc(age)
        return hours * p.childcare_funding_rate.calc(age)

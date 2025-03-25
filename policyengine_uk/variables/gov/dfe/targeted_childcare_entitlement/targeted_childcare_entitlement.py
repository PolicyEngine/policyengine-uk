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
        eligible_by_age = (
            p.targeted_childcare_entitlement.age_eligibility.calc(age)
        )
        hours = (
            p.targeted_childcare_entitlement.hours_entitlement
            * eligible_by_age
        )
        return hours * p.childcare_funding_rate.calc(age)

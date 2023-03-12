from policyengine_uk.model_api import *


class childcare_universal_entitlement(Variable):
    label = "Universal childcare entitlement"
    documentation = "Value of entitlement under the universal provision to 3-4 year olds"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(person, period, parameters):
        pass


class childcare_universal_entitlement_eligible_child(Variable):
    label = "eligible child for universal childcare entitlement"
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        age = person("age", period)
        conditions = parameters(period).gov.dfe.childcare.universal.age
        return (age >= conditions.min) & (age <= conditions.max)
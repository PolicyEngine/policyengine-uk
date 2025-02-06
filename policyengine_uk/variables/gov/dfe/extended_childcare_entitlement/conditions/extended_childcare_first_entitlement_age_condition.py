from policyengine_uk.model_api import *


class extended_childcare_first_entitlement_age_condition(Variable):
    value_type = bool
    entity = Person
    label = "Extended childcare first entitlement age eligibility"
    documentation = "Whether this child meets the age requirements for extended childcare entitlement based on age scale thresholds"
    definition_period = YEAR

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.dfe.extended_childcare_entitlement.age_eligibility
        return p.first_entitlement.calc(person("age", period))

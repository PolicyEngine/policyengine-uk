from policyengine_uk.model_api import *


class extended_childcare_second_entitlement_age_condition(Variable):
    value_type = bool
    entity = Person
    label = "Extended childcare second entitlement age eligibility"
    documentation = "Whether this child meets the age requirements for extended childcare entitlement based on age scale thresholds"
    definition_period = YEAR

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.dfe.extended_childcare_entitlement.age_eligibility
        return p.second_entitlement.calc(person("age", period))

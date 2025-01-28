from policyengine_uk.model_api import *


class universal_childcare_entitlement_eligibility(Variable):
    value_type = bool
    entity = BenUnit
    label = "universal childcare entitlement eligibility"
    documentation = "Whether the benefit unit has any children eligible for universal childcare entitlement"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        # Get parameters
        p = parameters(period).gov.dwp.universal_childcare_entitlement.age
        age = benunit.members("age", period)
        
        return benunit.any(
            benunit.members("is_child", period) & 
            (age >= p.min_age) & 
            (age < p.max_age)
        )

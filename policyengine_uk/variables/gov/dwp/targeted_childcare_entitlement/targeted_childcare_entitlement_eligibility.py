from policyengine_uk.model_api import *


class targeted_childcare_entitlement_eligibility(Variable):
    value_type = bool
    entity = BenUnit
    label = "targeted childcare entitlement eligibility"
    documentation = "Whether the benefit unit has any children eligible for targeted childcare entitlement"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        # Get parameters
        p = parameters(period).gov.dwp.targeted_childcare_entitlement

        # Get ages of all members in the benefit unit
        age = benunit.members("age", period)

        # Check if they are children
        is_child = benunit.members("is_child", period)

        # Check if age is eligible using the bracket calculation
        is_eligible_age = p.child_age_eligible.calc(age)

        return benunit.any(is_child & is_eligible_age)

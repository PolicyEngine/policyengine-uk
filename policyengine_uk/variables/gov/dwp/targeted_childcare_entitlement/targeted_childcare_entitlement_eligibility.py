from policyengine_uk.model_api import *

class targeted_childcare_entitlement_eligibility(Variable):
    value_type = bool
    entity = BenUnit
    label = "targeted childcare entitlement eligibility"
    documentation = "Whether the benefit unit has any children eligible for targeted childcare entitlement"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        """
        Calculate eligibility for targeted childcare entitlement.
        Args:
            benunit: The benefit unit
            period: The time period
            parameters: Policy parameters
        Returns:
            bool: Whether the benefit unit has any eligible children
        """
        # Get parameters
        p = parameters(period).gov.dwp.targeted_childcare_entitlement.age

        # Get ages of all members in the benefit unit
        age = benunit.members("age", period)

        # Check if they are children
        is_child = benunit.members("is_child", period)

        # Check if age is within eligible range using parameters
        is_eligible_age = (age >= p.min_age) & (age <= p.max_age)

        # Child must be within age range and officially counted as a child
        has_eligible_child = benunit.any(is_child & is_eligible_age)

        return has_eligible_child.astype(bool)
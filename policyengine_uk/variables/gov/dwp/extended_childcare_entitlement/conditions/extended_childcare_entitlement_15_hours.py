from policyengine_uk.model_api import *


class extended_childcare_entitlement_15_hours(Variable):
    value_type = bool
    entity = Person
    label = "Free childcare 15 hours eligibility"
    documentation = "Whether this child meets the age requirements for 15 hours of extended childcare entitlement"
    definition_period = YEAR  # Evaluate eligibility on a yearly basis

    def formula(person, period, parameters):
        """
        Determine if a child is eligible for 15 hours of extended childcare entitlement based on age.

        Returns:
            bool: True if the child is eligible for 15 hours, False otherwise.
        """
        # Get the child's age
        age = person("age", period)

        # Retrieve age thresholds
        age_limits = parameters(
            period
        ).gov.dwp.extended_childcare_entitlement.age
        lower_limit = age_limits.lower_limit_for_first_entitlement
        upper_limit = age_limits.upper_limit_for_first_entitlement

        # Check if the child is eligible
        eligible_15_hours = (age >= lower_limit) & (
            age <= upper_limit
        )

        # Return the eligibility status
        return eligible_15_hours.astype(bool)

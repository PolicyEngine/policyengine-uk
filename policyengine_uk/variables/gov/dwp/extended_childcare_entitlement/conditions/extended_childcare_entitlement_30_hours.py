from policyengine_uk.model_api import *


class extended_childcare_entitlement_30_hours(Variable):
    value_type = bool
    entity = Person
    label = "Extended childcare entitlement 30 hours eligibility"
    documentation = "Whether this child meets the age requirements for 30 hours of extended childcare entitlement"
    definition_period = YEAR  # Evaluate eligibility on a yearly basis

    def formula(person, period, parameters):
        """
        Determine if a child is eligible for 30 hours of extended childcare entitlement based on age.

        Returns:
            bool: True if the child is eligible for 30 hours, False otherwise.
        """
        # Get the child's age
        age = person("age", period)

        # Retrieve age thresholds
        age_limits = parameters(
            period
        ).gov.dwp.extended_childcare_entitlement.age
        lower_limit = age_limits.lower_limit_for_second_entitlement
        upper_limit = age_limits.upper_limit_for_second_entitlement

        # Check if the child is eligible
        eligible_30_hours = (age >= lower_limit) & (
            age <= upper_limit
        )

        # Return the eligibility status
        return eligible_30_hours.astype(bool)

from policyengine_uk.model_api import *


class free_childcare_15_hours(Variable):
    value_type = bool
    entity = Person
    label = "Free childcare 15 hours eligibility"
    documentation = "Whether this child meets the age requirements for 15 hours of free childcare"
    definition_period = YEAR  # Evaluate eligibility on a yearly basis

    def formula(person, period, parameters):
        """
        Determine if a child is eligible for 15 hours of free childcare based on age.

        Returns:
            bool: True if the child is eligible for 15 hours, False otherwise.
        """
        # Get the child's age
        age = person("age", period)

        # Retrieve age thresholds for 15 hours eligibility
        age_limits = parameters(
            period
        ).gov.dwp.childcare_subsidies.free_childcare.age
        lower_limit_9_months = age_limits.lower_limit_9_months
        upper_limit_3_years = age_limits.upper_limit_3_years

        # Check if the child is eligible for 15 hours (between 3 and 4 years old)
        eligible_15_hours = (age >= lower_limit_9_months) & (age <= upper_limit_3_years)

        # Return the eligibility status
        return eligible_15_hours.astype(bool)

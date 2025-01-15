from policyengine_uk.model_api import *


class free_childcare_30_hours(Variable):
    value_type = bool
    entity = Person
    label = "Free childcare 30 hours eligibility"
    documentation = "Whether this child meets the age requirements for 30 hours of free childcare"
    definition_period = YEAR  # Evaluate eligibility on a yearly basis

    def formula(person, period, parameters):
        """
        Determine if a child is eligible for 30 hours of free childcare based on age.

        Returns:
            bool: True if the child is eligible for 30 hours, False otherwise.
        """
        # Get the child's age
        age = person("age", period)

        # Retrieve age thresholds for 30 hours eligibility
        age_limits = parameters(
            period
        ).gov.dwp.childcare_subsidies.free_childcare.age
        lower_limit_3_years = age_limits.lower_limit_3_years
        upper_limit_4_years = age_limits.upper_limit_4_years

        # Check if the child is eligible for 30 hours (between 3 and 4 years old)
        eligible_30_hours = (age >= lower_limit_3_years) & (age <= upper_limit_4_years)

        # Return the eligibility status
        return eligible_30_hours.astype(bool)

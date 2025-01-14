from policyengine_uk.model_api import *


class child_age_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Child age eligibility requirements"
    documentation = (
        "Whether this person meets the age and disability requirements for eligibility"
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        """
        Calculate age eligibility based on age and disability conditions.

        Returns:
            bool: True if eligible (under standard age limit, or under disability age limit with disability), False otherwise
        """
        # Get person's characteristics
        age = person("age", period)

        # Get age thresholds from parameters
        age_limits = parameters(
            period
        ).gov.dwp.childcare_subsidies.tax_free_childcare.age
        standard_age_limit = age_limits.standard
        disability_age_limit = age_limits.disability

        # Check disability status
        is_disabled = person("is_disabled_for_benefits", period)

        # Check age conditions using parameterized values
        basic_age_condition = (age < standard_age_limit).astype(bool)
        age_under_disability_limit = (age < disability_age_limit).astype(bool)

        # Combine conditions
        combined_condition = (age_under_disability_limit & is_disabled).astype(bool)
        return (basic_age_condition | combined_condition).astype(bool)

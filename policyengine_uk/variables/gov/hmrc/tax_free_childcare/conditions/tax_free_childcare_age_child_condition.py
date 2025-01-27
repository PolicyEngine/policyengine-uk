from policyengine_uk.model_api import *


class tax_free_childcare_child_age_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Eligible child for the tax-free childcare"
    documentation = "Whether this person meets the age and disability requirements for eligibility"
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
        age_limits = parameters(period).gov.hmrc.tax_free_childcare.age

        # Check disability status
        is_disabled = person("is_disabled_for_benefits", period)
        is_blind = person("is_blind", period)

        # Check age conditions using parameterized values
        basic_age_condition = age < age_limits.standard
        age_under_disability_limit = age < age_limits.disability

        # Combine conditions
        combined_condition = age_under_disability_limit & (is_disabled | is_blind)
        return basic_age_condition | combined_condition

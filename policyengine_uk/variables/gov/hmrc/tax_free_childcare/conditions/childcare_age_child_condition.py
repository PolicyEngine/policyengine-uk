from policyengine_uk.model_api import *

class child_age_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Child age eligibility requirements"
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
        age_limits = parameters(
            period
        ).gov.hmrc.childcare_subsidies.tax_free_childcare.age
        standard_age_limit = age_limits.standard
        disability_age_limit = age_limits.disability

        # Check disability conditions
        gc = parameters(
            period
        ).gov.dwp.pension_credit.guarantee_credit.child.disability
        standard_disability_benefits = gc.eligibility
        severe_disability_benefits = gc.severe.eligibility

        # Convert to boolean arrays before combining
        standard_benefits = add(person, period, standard_disability_benefits).astype(bool)
        severe_benefits = add(person, period, severe_disability_benefits).astype(bool)
        is_disabled = (standard_benefits | severe_benefits)

        # Check age conditions using parameterized values
        basic_age_condition = age < standard_age_limit
        age_under_disability_limit = age < disability_age_limit

        # Convert to boolean before final combination
        return (basic_age_condition.astype(bool) | 
                (age_under_disability_limit.astype(bool) & is_disabled))
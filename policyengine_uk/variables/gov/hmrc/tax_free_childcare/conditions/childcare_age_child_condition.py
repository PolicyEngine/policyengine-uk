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
        # Get the benefit unit the person belongs to
        benunit = person.benunit

        # Get person's characteristics
        age = person("age", period)

        # Get age thresholds from parameters
        age_limits = parameters(period).gov.hmrc.childcare_subsidies.tax_free_childcare.age_limits
        standard_age_limit = age_limits.standard_age_limit
        disability_age_limit = age_limits.disability_age_limit

        # Check disability conditions
        gc = parameters(period).gov.dwp.pension_credit.guarantee_credit
        standard_disability_benefits = gc.child.disability.eligibility
        severe_disability_benefits = gc.child.disability.severe.eligibility

        is_disabled = (
            add(person, period, standard_disability_benefits)
            | add(person, period, severe_disability_benefits)
        ) > 0

        # Check age conditions using parameterized values
        basic_age_condition = age < standard_age_limit
        age_under_disability_limit = age < disability_age_limit

        # Combine conditions
        eligible = basic_age_condition | (age_under_disability_limit & is_disabled)

        return eligible
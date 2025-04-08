from policyengine_uk.model_api import *


class care_to_learn_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible for Care to Learn childcare support"
    definition_period = YEAR
    defined_for = "would_claim_care_to_learn"

    def formula(person, period, parameters):
        # Link for instruction: https://www.gov.uk/care-to-learn/eligibility

        # Only parents can be eligible, not children
        is_parent = person("is_parent", period)

        # Check basic eligibility conditions
        benunit_has_children = person.benunit.any(person("is_child", period))
        p = parameters(period).gov.dfe.care_to_learn
        age_eligible = person("age", period) < p.age_limit

        current_ed = person("current_education", period)
        education_types = current_ed.possible_values

        # Only exclude higher education/tertiary
        not_higher_education = current_ed != education_types.TERTIARY

        not_apprentice = ~person("is_apprentice", period)

        # Check if person lives in England
        country = person.household("country", period)
        countries = country.possible_values
        lives_in_england = country == countries.ENGLAND

        return (
            is_parent
            & benunit_has_children
            & age_eligible
            & not_higher_education
            & lives_in_england
            & not_apprentice
        )

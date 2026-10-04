from policyengine_uk.model_api import *


class care_to_learn_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible for Care to Learn childcare support"
    definition_period = YEAR
    defined_for = "would_claim_care_to_learn"
    reference = (
        "https://www.gov.uk/government/publications/care-to-learn-conditions-of-grant-funding/care-to-learn-academic-year-2026-to-2027-conditions-of-grant-funding",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/142",
    )

    def formula(person, period, parameters):
        # Link for instruction: https://www.gov.uk/care-to-learn/eligibility

        # Only parents can be eligible, not children
        is_parent = person("is_parent", period)

        # The young parent must be the main carer of, and receive Child
        # Benefit for, the child they claim for (ESFA conditions of grant).
        # So the child is a Child Benefit child or qualifying young person in
        # the benefit unit, other than the parent themselves.
        cares_for_child_benefit_child = person.benunit.any(
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
            & ~is_parent
        )
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
            & cares_for_child_benefit_child
            & age_eligible
            & not_higher_education
            & lives_in_england
            & not_apprentice
        )

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
        # Benefit for, a child they claim for (ESFA conditions of grant,
        # section 2.2).
        cares_for_qualifying_child = person.benunit.any(
            person("care_to_learn_qualifying_child", period)
        )
        p = parameters(period).gov.dfe.care_to_learn
        age_eligible = person("age", period) < p.age_limit

        # Care to Learn funds childcare while the young parent is on a
        # publicly funded study programme (sections 1.2 and 2.3). Higher
        # education courses are not eligible, and a young parent who is not
        # in education has no study programme to fund childcare for.
        current_ed = person("current_education", period)
        education_types = current_ed.possible_values
        on_study_programme = (current_ed != education_types.NOT_IN_EDUCATION) & (
            current_ed != education_types.TERTIARY
        )

        not_apprentice = ~person("is_apprentice", period)

        # Check if person lives in England
        country = person.household("country", period)
        countries = country.possible_values
        lives_in_england = country == countries.ENGLAND

        return (
            is_parent
            & cares_for_qualifying_child
            & age_eligible
            & on_study_programme
            & lives_in_england
            & not_apprentice
        )

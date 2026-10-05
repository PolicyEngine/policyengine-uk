from policyengine_uk.model_api import *


class care_to_learn_qualifying_child(Variable):
    value_type = bool
    entity = Person
    label = "child a young parent can claim Care to Learn for"
    documentation = (
        "A child in the benefit unit whom a young parent can claim Care to "
        "Learn for. The young parent must be the main carer of, and receive "
        "Child Benefit for, the child they claim for (ESFA conditions of "
        "grant, section 2.2), so the child is a Child Benefit child or "
        "qualifying young person in the benefit unit other than a parent."
    )
    definition_period = YEAR
    reference = (
        "https://www.gov.uk/government/publications/care-to-learn-conditions-of-grant-funding/care-to-learn-academic-year-2026-to-2027-conditions-of-grant-funding",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/142",
    )

    def formula(person, period, parameters):
        return person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        ) & ~person("is_parent", period)

from policyengine_uk.model_api import *


class is_qualifying_young_person_for_child_benefit(Variable):
    value_type = bool
    entity = Person
    label = "Qualifying young person for Child Benefit"
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/ukpga/1992/4/section/142",
        "https://www.legislation.gov.uk/uksi/2006/223",
    ]

    def formula(person, period, parameters):
        return (
            person(
                "meets_qualifying_young_person_age_condition_for_child_benefit",
                period,
            )
            & person(
                "meets_qualifying_young_person_education_or_training_condition_for_child_benefit",
                period,
            )
            & person(
                "meets_qualifying_young_person_entry_condition_for_child_benefit",
                period,
            )
            & ~person("receives_benefits_in_own_right", period)
        )

from policyengine_uk.model_api import *


class meets_qualifying_young_person_education_or_training_condition_for_child_benefit(
    Variable
):
    value_type = bool
    entity = Person
    label = (
        "Meets qualifying young person education or training condition for "
        "Child Benefit"
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2006/223"

    def formula(person, period, parameters):
        return person("is_in_non_advanced_education", period) | person(
            "is_in_approved_training", period
        )

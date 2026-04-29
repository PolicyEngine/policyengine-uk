from policyengine_uk.model_api import *


class is_qualifying_young_person_for_child_tax_credit(Variable):
    value_type = bool
    entity = Person
    label = "Qualifying young person for Child Tax Credit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/regulation/5"

    def formula(person, period, parameters):
        return (
            person(
                "meets_qualifying_young_person_age_condition_for_child_tax_credit",
                period,
            )
            & person(
                "meets_qualifying_young_person_education_or_training_condition_for_child_tax_credit",
                period,
            )
            & person(
                "meets_qualifying_young_person_entry_condition_for_child_tax_credit",
                period,
            )
            & ~person("receives_benefits_in_own_right", period)
        )

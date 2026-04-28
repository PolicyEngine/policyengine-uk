from policyengine_uk.model_api import *


class is_child_or_qualifying_young_person_for_pension_credit(Variable):
    value_type = bool
    entity = Person
    label = "Child or qualifying young person for Pension Credit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IIA"

    def formula(person, period, parameters):
        child_or_qualifying_young_person = person(
            "is_child_for_pension_credit", period
        ) | person("is_qualifying_young_person_for_pension_credit", period)
        return child_or_qualifying_young_person & ~person(
            "is_looked_after_by_local_authority", period
        )

from policyengine_uk.model_api import *


class is_child_or_qualifying_young_person_for_universal_credit(Variable):
    value_type = bool
    entity = Person
    label = "Child or qualifying young person for Universal Credit"
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
    ]

    def formula(person, period, parameters):
        child_or_qualifying_young_person = person(
            "is_child_for_universal_credit", period
        ) | person("is_qualifying_young_person_for_universal_credit", period)
        return child_or_qualifying_young_person & ~person(
            "is_looked_after_by_local_authority", period
        )

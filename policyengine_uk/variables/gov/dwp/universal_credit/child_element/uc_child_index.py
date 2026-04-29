from policyengine_uk.model_api import *


class uc_child_index(Variable):
    value_type = int
    entity = Person
    label = "Universal Credit child reference number"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/24A"

    def formula(person, period, parameters):
        is_uc_child = person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        )
        child_ranking = (
            person.get_rank(
                person.benunit,
                -person("age", period),
                condition=is_uc_child,
            )
            + 1
        )
        return where(is_uc_child, child_ranking, -1)

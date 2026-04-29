from policyengine_uk.model_api import *


class child_benefit_child_index(Variable):
    value_type = int
    entity = Person
    label = "Child Benefit child reference number"
    definition_period = YEAR

    def formula(person, period, parameters):
        child = person("is_child_or_qualifying_young_person_for_child_benefit", period)
        rank = (
            person.get_rank(
                person.benunit,
                -person("age", period),
                condition=child,
            )
            + 1
        )
        return where(child, rank, -1)

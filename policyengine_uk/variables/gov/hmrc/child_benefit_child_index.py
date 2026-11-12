from policyengine_uk.model_api import *


class child_benefit_child_index(Variable):
    value_type = int
    entity = Person
    label = "Child Benefit child reference number"
    definition_period = YEAR

    def formula(person, period, parameters):
        child = person("is_child_benefit_payable_for_person", period)
        rank = (
            person.get_rank(
                person.benunit,
                -person("age", period),
                condition=child,
            )
            + 1
        )
        return where(child, rank, -1)

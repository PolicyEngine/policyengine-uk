from policyengine_uk.model_api import *
import pandas as pd


class child_index(Variable):
    value_type = int
    entity = Person
    label = "Child reference number"
    definition_period = YEAR

    def formula(person, period, parameters):
        # The child index, by age, descending (e.g. "first child" = 1)
        is_child = person("is_child", period)
        child_ranking = (
            person.get_rank(
                person.benunit,
                -person("age", period),
                condition=is_child,
            )
            + 1
        )
        return where(is_child, child_ranking, -1)

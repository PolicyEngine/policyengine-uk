from policyengine_uk.model_api import *
import pandas as pd


class child_index(Variable):
    value_type = int
    entity = Person
    label = "Child reference number"
    definition_period = YEAR

    def formula(person, period, parameters):
        # The child index, by age, descending (e.g. "first child" = 1)
        child_ranking = (
            person.get_rank(
                person.benunit,
                -person("age", period),
            )
            + 1
        )
        # Fill in adult values
        values = where(person("is_child", period), child_ranking, 100)
        # Base to 0
        values = values - person.benunit.min(values) + 1
        return where(person("is_child", period), values, -1)

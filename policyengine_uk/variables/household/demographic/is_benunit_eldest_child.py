from policyengine_uk.model_api import *
import pandas as pd


class is_benunit_eldest_child(Variable):
    value_type = bool
    entity = Person
    label = "Eldest child in the benefit unit"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        is_child = person("is_child", period)
        eldest_age = person.benunit("eldest_child_age", period)
        age_tie = person.benunit.sum((age == eldest_age) & is_child) > 1
        is_eldest_age = person("age", period) == eldest_age
        child_id = person("person_id", period) * is_child
        max_child_id = person.benunit.max(child_id)
        has_max_child_id = child_id == max_child_id
        return where(is_eldest_age & age_tie, has_max_child_id, is_eldest_age)

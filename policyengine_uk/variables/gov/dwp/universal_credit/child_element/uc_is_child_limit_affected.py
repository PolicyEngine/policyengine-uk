from policyengine_uk.model_api import *


class uc_is_child_limit_affected(Variable):
    label = "affected by the UC child limit"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        return (
            (person("uc_individual_child_element", period) == 0)
            & person("is_child", period)
            & (person.benunit("universal_credit", period) > 0)
        )

from policyengine_uk.model_api import *


class count_children_and_qyp(Variable):
    label = "Children and qualifying young people"
    documentation = "The number of children and qualifying young people (young adults in education) in the family"
    entity = BenUnit
    definition_period = YEAR
    value_type = int
    unit = GBP

    def formula(benunit, period, parameters):
        return add(benunit, period, ["is_child_or_QYP"])

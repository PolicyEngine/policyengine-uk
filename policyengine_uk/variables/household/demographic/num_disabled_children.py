from policyengine_uk.model_api import *


class num_disabled_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of disabled children"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        child = benunit.members("is_child_or_QYP", period)
        disabled = benunit.members("is_disabled_for_benefits", period)
        return benunit.sum(child & disabled)

from policyengine_uk.model_api import *


class is_uc_work_allowance_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Family receives a Universal Credit Work Allowance"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        person = benunit.members
        has_lcwra = benunit.any(
            person("uc_limited_capability_for_WRA", period)
        )
        has_children = benunit.any(person("is_child", period))
        return has_lcwra | has_children

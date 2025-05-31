from policyengine_uk.model_api import *


class income_support_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether eligible for Income Support"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        youngest_child_5_or_under = benunit("youngest_child_age", period) <= 5
        lone_parent = benunit("is_lone_parent", period)
        lone_parent_with_young_child = lone_parent & youngest_child_5_or_under
        has_carers = add(benunit, period, ["is_carer_for_benefits"]) > 0
        none_SP_age = ~benunit.any(benunit.members("is_SP_age", period))
        has_esa_income = benunit("esa_income", period) > 0
        already_claiming = (
            add(benunit, period, ["income_support_reported"]) > 0
        )
        return (
            (has_carers | lone_parent_with_young_child)
            & none_SP_age
            & ~has_esa_income
            & already_claiming
        )

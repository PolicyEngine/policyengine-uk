from policyengine_uk.model_api import *


class extended_childcare_entitlement_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether this benefit unit is eligible for extended childcare entitlement"
    documentation = "Checks if the benefit unit meets all eligibility conditions (work and income requirements) for extended childcare entitlement"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        # Check income condition - must be true for all family members (except children)
        person = benunit.members
        person_meets_income_condition = person(
            "extended_childcare_entitlement_meets_income_requirements",
            period,
        ) | person("is_child", period)
        meets_income_condition = benunit.all(person_meets_income_condition)

        # Check work condition
        work_eligible = (
            benunit("extended_childcare_entitlement_work_condition", period)
            > 0
        )

        return meets_income_condition & work_eligible

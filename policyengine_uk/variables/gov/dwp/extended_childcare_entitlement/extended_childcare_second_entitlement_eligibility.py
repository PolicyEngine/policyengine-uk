from policyengine_uk.model_api import *


class extended_childcare_second_entitlement_eligibility(Variable):
    value_type = bool
    entity = BenUnit
    label = "Extended childcare second entitlement total eligibility"
    documentation = "Whether the benefit unit is eligible for extended childcare second entitlement"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        # Age eligibility
        age_eligible = benunit.any(
            benunit.members(
                "extended_childcare_second_entitlement_age_condition", period
            )
        )

        # Income requirements
        meets_income = benunit.any(
            benunit.members(
                "extended_childcare_entitlement_meets_income_requirements",
                period,
            )
        )

        # Alternative eligibility
        alternative_eligible = benunit.any(
            benunit.members(
                "extended_childcare_entitlement_work_condition", period
            )
        )

        return age_eligible & meets_income & alternative_eligible

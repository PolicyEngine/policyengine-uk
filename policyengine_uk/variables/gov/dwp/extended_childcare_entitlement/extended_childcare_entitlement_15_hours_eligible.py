from policyengine_uk.model_api import *


class extended_childcare_entitlement_15_hours_eligibility(Variable):
    value_type = bool
    entity = BenUnit
    label = "Extended childcare entitlement 15 hours eligibility"
    documentation = "Whether the benefit unit is eligible for extended childcare entitlement 15 hours"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        """
        Calculate eligibility for 15 hours free childcare program.
        """
        # Age eligibility
        age_eligible = benunit.any(
            benunit.members("extended_childcare_entitlement_15_hours", period)
        )

        # Income requirements
        meets_income = benunit.any(
            benunit.members(
                "extended_childcare_entitlement_income_requirements", period
            )
        )

        # Alternative eligibility
        alternative_eligible = benunit.any(
            benunit.members(
                "extended_childcare_entitlement_work_eligibility", period
            )
        )

        return (age_eligible & meets_income & alternative_eligible).astype(
            bool
        )

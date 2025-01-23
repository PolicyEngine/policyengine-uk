from policyengine_uk.model_api import *


class tax_free_childcare_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Overall eligibility for tax-free childcare"
    documentation = (
        "Combined result of all tax-free childcare eligibility conditions"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        """
        Combines all eligibility conditions for tax-free childcare using logical AND.

        Args:
            benunit: The benefit unit
            period: The time period
            parameters: Policy parameters

        Returns:
            bool: Whether all eligibility conditions are met
        """
        meets_age_condition = benunit(
            "tax_free_childcare_child_age_eligible", period
        )

        meets_income_condition = benunit.any(
            benunit.members(
                "tax_free_childcare_meets_income_requirements", period
            )
        )

        childcare_eligible = benunit(
            "tax_free_childcare_program_eligible", period
        )

        work_eligible = benunit("tax_free_childcare_work_condition", period)

        return np.logical_and.reduce(
            [
                meets_age_condition,
                meets_income_condition,
                childcare_eligible,
                work_eligible,
            ]
        )

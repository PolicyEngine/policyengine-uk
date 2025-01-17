from policyengine_uk.model_api import *


class tax_free_childcare_overall_eligible(Variable):
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
        ).astype(bool)

        meets_income_condition = benunit.any(
            benunit.members(
                "tax_free_childcare_meets_income_requirements", period
            )
        ).astype(bool)

        childcare_eligible = benunit(
            "tax_free_childcare_incompatibilities_childcare_eligible", period
        ).astype(bool)

        work_eligible = benunit(
            "tax_free_childcare_work_condition", period
        ).astype(bool)

        return np.logical_and.reduce(
            [
                meets_age_condition,
                meets_income_condition,
                childcare_eligible,
                work_eligible,
            ]
        )


class tax_free_childcare(Variable):
    value_type = float
    entity = BenUnit
    label = "Tax-free childcare government contribution"
    documentation = "The amount of government contribution provided through the tax-free childcare scheme"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        """
        Calculate the government contribution for tax-free childcare.

        Args:
            benunit: The benefit unit
            period: The time period
            parameters: Policy parameters

        Returns:
            float: The calculated government contribution
        """
        # Get parameters
        p_tfc = parameters(
            period
        ).gov.dwp.childcare_subsidies.tax_free_childcare.contribution

        # Get eligibility from separate class
        is_eligible = benunit("tax_free_childcare_overall_eligible", period)

        # Calculate per-child amounts at the person level
        is_child = benunit.members("is_child", period)
        is_disabled = benunit.members("is_disabled_for_benefits", period)

        child_amounts = where(
            is_child,
            where(is_disabled, p_tfc.disabled_child, p_tfc.standard_child),
            0,
        )

        # Reduce to benefit unit level by taking maximum
        max_amount = benunit.max(child_amounts)

        # Apply final eligibility check
        return where(is_eligible, max_amount, 0)

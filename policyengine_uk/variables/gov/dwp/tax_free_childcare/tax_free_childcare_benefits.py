from policyengine_uk.model_api import *


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

        # Check eligibility conditions with explicit type conversion
        meets_age_condition = benunit("child_age_eligible", period).astype(
            bool
        )
        meets_income_condition = benunit.any(
            benunit.members("meets_income_requirements", period)
        ).astype(bool)
        childcare_eligible = benunit(
            "incompatibilities_childcare_eligible", period
        ).astype(bool)

        is_eligible = (
            meets_age_condition & meets_income_condition & childcare_eligible
        )

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

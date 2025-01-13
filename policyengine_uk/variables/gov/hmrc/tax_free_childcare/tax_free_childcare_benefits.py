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
        # Get parameters from the parameter tree
        p = parameters(
            period
        ).gov.hmrc.childcare_subsidies.tax_free_childcare.contribution

        # Check eligibility conditions
        meets_age_condition = benunit("child_age_eligible", period)
        meets_income_condition = benunit.any(
            benunit.members("meets_income_requirements", period)
        )
        is_eligible = (
            meets_age_condition
            & meets_income_condition
            & benunit("incompatibilities_childcare_eligible", period)
        )

        # Determine the maximum eligible childcare cost for a single child
        max_amount = 0
        for child in benunit.members("is_child", period):
            max_amount = where(
                is_eligible[child],
                where(
                    child("is_disabled", period),
                    p.disabled_child.values,
                    p.standard_child.values
                ),
                max_amount
            )

        return where(is_eligible, max_amount, 0)
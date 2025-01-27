from policyengine_uk.model_api import *


class tax_free_childcare_benefits_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "Tax-free childcare government contribution"
    documentation = "The amount of government contribution provided through the tax-free childcare scheme"
    definition_period = YEAR
    unit = GBP
    defined_for = "tax_free_childcare_eligible"

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
        p = parameters(period).gov.hmrc.tax_free_childcare.contribution

        # Get eligibility from separate class
        is_eligible = benunit("tax_free_childcare_eligible", period)

        # Calculate per-child amounts at the person level
        person = benunit.members
        is_child = person("is_child", period)
        is_disabled = person("is_disabled_for_benefits", period)
        is_blind = person("is_blind", period)

        # Child gets higher amount if either disabled or blind
        qualifies_for_higher_amount = is_disabled | is_blind

        amount_per_child = (
            where(
                qualifies_for_higher_amount, p.disabled_child, p.standard_child
            )
        ) * is_child

        # Reduce to benefit unit level by taking maximum
        return benunit.sum(amount_per_child)

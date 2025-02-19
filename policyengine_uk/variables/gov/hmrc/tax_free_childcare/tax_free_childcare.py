from policyengine_uk.model_api import *


class tax_free_childcare(Variable):
    value_type = float
    entity = BenUnit
    label = "Tax-free childcare government contribution"
    documentation = "The amount of government contribution provided through the tax-free childcare scheme"
    definition_period = YEAR
    unit = GBP
    defined_for = "tax_free_childcare_eligible"

    def formula(benunit, period, parameters):
        # Get parameters
        p = parameters(period).gov.hmrc.tax_free_childcare.contribution

        # Calculate per-child amounts at the person level
        person = benunit.members
        is_child = person("is_child", period)
        is_disabled = person("is_disabled_for_benefits", period)
        is_blind = person("is_blind", period)

        # Child gets higher amount if either disabled or blind
        qualifies_for_higher_amount = is_disabled | is_blind

        # Get childcare expenses
        childcare_expenses = benunit.members("childcare_expenses", period)

        # Calculate contribution using rate from parameters
        contribution = childcare_expenses * p.rate

        # Cap the contribution at the maximum amounts
        max_amounts = (
            where(
                qualifies_for_higher_amount, p.disabled_child, p.standard_child
            )
            * is_child
        )

        capped_contribution = min_(contribution, max_amounts)

        # Sum across all children in the benefit unit
        return benunit.sum(capped_contribution)

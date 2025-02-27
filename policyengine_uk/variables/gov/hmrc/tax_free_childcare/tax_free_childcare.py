from policyengine_uk.model_api import *


class tax_free_childcare(Variable):
    value_type = float
    entity = Person
    label = "government contribution through tax-free childcare"
    definition_period = YEAR
    unit = GBP
    defined_for = "tax_free_childcare_eligible"
    # Note: tax_free_childcare_eligible is a BenUnit variable implicitly cast to Person level

    def formula(person, period, parameters):
        # Get parameters
        p = parameters(period).gov.hmrc.tax_free_childcare.contribution

        # Calculate per-person amounts
        is_parent = person("is_parent", period)
        is_disabled = person("is_disabled_for_benefits", period)
        is_blind = person("is_blind", period)

        # Person gets higher amount if either disabled or blind
        qualifies_for_higher_amount = is_disabled | is_blind

        # Get childcare expenses
        childcare_expense = person("childcare_expenses", period)

        # Calculate contribution using rate from parameters
        contribution = (childcare_expense * p.rate) / (1 - p.rate)

        # Cap the contribution at the maximum amounts
        max_amount = (
            where(
                qualifies_for_higher_amount, p.disabled_child, p.standard_child
            )
            * ~is_parent
        )

        return min_(contribution, max_amount)

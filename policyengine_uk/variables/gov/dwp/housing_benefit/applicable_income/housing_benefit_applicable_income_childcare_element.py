from policyengine_uk.model_api import *


class housing_benefit_applicable_income_childcare_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit applicable income childcare element"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.tax_credits.working_tax_credit.elements
        num_children = benunit("benunit_count_children", period)
        childcare_amount_1 = (num_children == 1) * p.childcare_1
        childcare_amount_2 = (num_children > 1) * p.childcare_2
        max_weekly_childcare_amount = childcare_amount_1 + childcare_amount_2
        # Assuming that no children leads to no childcare element
        capped_max_childcare_amount = where(
            num_children == 0, 0, max_weekly_childcare_amount
        )
        max_childcare_amount = capped_max_childcare_amount * WEEKS_IN_YEAR
        childcare_expenses = add(benunit, period, ["childcare_expenses"])
        return min_(
            max_childcare_amount,
            childcare_expenses,
        )

from policyengine_uk.model_api import *


class WTC_childcare_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit childcare element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = GBP
    defined_for = "is_WTC_eligible"

    def formula(benunit, period, parameters):
        WTC = parameters(period).gov.dwp.tax_credits.working_tax_credit
        num_children = benunit("num_children", period)
        childcare_1 = (num_children == 1) * WTC.elements.childcare_1
        childcare_2 = (num_children > 1) * WTC.elements.childcare_2
        max_childcare_amount = (childcare_1 + childcare_2) * WEEKS_IN_YEAR
        expenses = add(benunit, period, ["childcare_expenses"])
        eligible_expenses = min_(max_childcare_amount, expenses)
        return WTC.elements.childcare_coverage * eligible_expenses

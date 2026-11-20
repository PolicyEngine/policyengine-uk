from policyengine_uk.model_api import *


class WTC_childcare_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit childcare element"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/2005/regulation/14",
        "https://www.legislation.gov.uk/uksi/2002/2005/regulation/20",
    )
    unit = GBP
    defined_for = "is_WTC_eligible"

    def formula(benunit, period, parameters):
        WTC = parameters(period).gov.dwp.tax_credits.working_tax_credit
        num_childcare_children = add(
            benunit, period, ["is_child_for_working_tax_credit_childcare_element"]
        )
        childcare_1 = (num_childcare_children == 1) * WTC.elements.childcare_1
        childcare_2 = (num_childcare_children > 1) * WTC.elements.childcare_2
        max_childcare_amount = (childcare_1 + childcare_2) * WEEKS_IN_YEAR
        expenses = add(benunit, period, ["childcare_expenses"])
        eligible_expenses = min_(max_childcare_amount, expenses)
        return WTC.elements.childcare_coverage * eligible_expenses

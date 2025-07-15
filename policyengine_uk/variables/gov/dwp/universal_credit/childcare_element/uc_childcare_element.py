from policyengine_uk.model_api import *


class uc_childcare_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit childcare element"
    definition_period = YEAR
    unit = GBP
    defined_for = "uc_childcare_work_condition"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.childcare
        eligible_childcare_expenses = add(
            benunit, period, ["childcare_expenses"]
        )
        covered_expenses = eligible_childcare_expenses * p.coverage_rate
        max_childcare = benunit("uc_maximum_childcare_element_amount", period)
        return min_(max_childcare, covered_expenses)

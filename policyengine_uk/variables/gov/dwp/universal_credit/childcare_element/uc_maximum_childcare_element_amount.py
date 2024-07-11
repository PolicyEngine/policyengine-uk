from policyengine_uk.model_api import *


class uc_maximum_childcare_element_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "Maximum Universal Credit childcare element"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.childcare
        children = benunit("uc_childcare_element_eligible_children", period)
        clipped_children_count = clip(children, 1, 2)
        max_amount = p.cap[clipped_children_count] * MONTHS_IN_YEAR
        return where(children == 0, 0, max_amount)

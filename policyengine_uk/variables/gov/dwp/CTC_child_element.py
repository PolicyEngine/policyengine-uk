from policyengine_uk.model_api import *


class CTC_child_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Child Tax Credit child element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"
    unit = GBP

    def formula(benunit, period, parameters):
        person = benunit.members
        child_tax_credit = parameters(period).gov.dwp.tax_credits.child_tax_credit
        child_or_qualifying_young_person = person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        is_child_limit_exempt = person("is_CTC_child_limit_exempt", period)
        exempt_child = child_or_qualifying_young_person & is_child_limit_exempt
        exempt_children = benunit.sum(exempt_child)
        child_limit = child_tax_credit.limit.child_count
        spaces_left = max_(0, child_limit - exempt_children)
        non_exempt_children = min_(
            spaces_left,
            benunit.sum(child_or_qualifying_young_person) - exempt_children,
        )
        children = exempt_children + non_exempt_children
        return child_tax_credit.elements.child_element * children

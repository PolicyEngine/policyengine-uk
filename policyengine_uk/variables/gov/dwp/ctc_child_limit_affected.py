from policyengine_uk.model_api import *


class ctc_child_limit_affected(Variable):
    label = "affected by the CTC child limit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

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
        return (
            exempt_children + non_exempt_children
            < benunit.sum(child_or_qualifying_young_person)
        ) & (benunit("child_tax_credit", period) > 0)

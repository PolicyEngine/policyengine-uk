from policyengine_uk.model_api import *


class ctc_child_limit_affected(Variable):
    label = "affected by the CTC child limit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        person = benunit.members
        CTC = parameters(period).gov.dwp.tax_credits.child_tax_credit
        is_child_for_CTC = person("is_child_for_CTC", period)
        is_CTC_child_limit_exempt = person("is_CTC_child_limit_exempt", period)
        exempt_child = is_child_for_CTC & is_CTC_child_limit_exempt
        exempt_children = benunit.sum(exempt_child)
        child_limit = CTC.limit.child_count
        spaces_left = max_(0, child_limit - exempt_children)
        non_exempt_children = min_(
            spaces_left, benunit.sum(is_child_for_CTC) - exempt_children
        )
        return (
            exempt_children + non_exempt_children
            < benunit.sum(is_child_for_CTC)
        ) & (benunit("child_tax_credit", period) > 0)

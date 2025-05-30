from policyengine_uk.model_api import *


class CTC_disabled_child_element(Variable):
    value_type = float
    entity = BenUnit
    label = "CTC entitlement from disabled child elements"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"
    unit = GBP

    def formula(benunit, period, parameters):
        person = benunit.members
        is_child_for_CTC = person("is_child_for_CTC", period)
        is_disabled_for_benefits = person("is_disabled_for_benefits", period)
        is_disabled_child = is_child_for_CTC & is_disabled_for_benefits
        disabled_children = benunit.sum(is_disabled_child)
        CTC = parameters(period).gov.dwp.tax_credits.child_tax_credit
        amount = CTC.elements.dis_child_element * disabled_children
        return benunit("is_CTC_eligible", period) * amount

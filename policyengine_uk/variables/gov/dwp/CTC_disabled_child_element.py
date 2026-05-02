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
        child_or_qualifying_young_person = person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        is_disabled_for_benefits = person("is_disabled_for_benefits", period)
        is_disabled_child = child_or_qualifying_young_person & is_disabled_for_benefits
        disabled_children = benunit.sum(is_disabled_child)
        child_tax_credit = parameters(period).gov.dwp.tax_credits.child_tax_credit
        amount = child_tax_credit.elements.dis_child_element * disabled_children
        return benunit("is_CTC_eligible", period) * amount

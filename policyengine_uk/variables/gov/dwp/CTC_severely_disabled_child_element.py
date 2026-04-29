from policyengine_uk.model_api import *


class CTC_severely_disabled_child_element(Variable):
    value_type = float
    entity = BenUnit
    label = "CTC entitlement from severely disabled child elements"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"
    unit = GBP
    defined_for = "is_CTC_eligible"

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_qualifying_young_person = person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        is_severely_disabled_for_benefits = person(
            "is_severely_disabled_for_benefits", period
        )
        is_severely_disabled_child = (
            child_or_qualifying_young_person & is_severely_disabled_for_benefits
        )
        severely_disabled_children = benunit.sum(is_severely_disabled_child)
        child_tax_credit = parameters(period).gov.dwp.tax_credits.child_tax_credit
        return (
            child_tax_credit.elements.severe_dis_child_element
            * severely_disabled_children
        )

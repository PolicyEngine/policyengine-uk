from policyengine_uk.model_api import *


class ctc_child_limit_affected(Variable):
    label = "affected by the CTC child limit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        person = benunit.members
        child_or_qualifying_young_person = person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        included = person("is_CTC_child_element_included", period)
        return (
            benunit.sum(included) < benunit.sum(child_or_qualifying_young_person)
        ) & (benunit("child_tax_credit", period) > 0)

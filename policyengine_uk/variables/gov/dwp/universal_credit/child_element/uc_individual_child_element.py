from policyengine_uk.model_api import *


class uc_individual_child_element(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit child element"
    documentation = "For this child, given Universal Credit eligibility"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        UC = parameters(period).gov.dwp.universal_credit
        child_index = person("child_index", period)
        born_before_limit = person(
            "uc_is_child_born_before_child_limit", period
        )
        child_limit_applying = where(
            ~born_before_limit, UC.elements.child.limit.child_count, inf
        )
        is_eligible = (child_index != -1) & (
            child_index <= child_limit_applying
        )
        return (
            select(
                [
                    (child_index == 1) & born_before_limit & is_eligible,
                    is_eligible,
                ],
                [
                    UC.elements.child.first.higher_amount,
                    UC.elements.child.amount,
                ],
                default=0,
            )
            * MONTHS_IN_YEAR
        )

from policyengine_uk.model_api import *


class uc_individual_child_element(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit child element"
    documentation = "For this child, given Universal Credit eligibility"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.child
        child_index = person("child_index", period)
        born_before_limit = person(
            "uc_is_child_born_before_child_limit", period
        )
        child_limit_applying = where(
            ~born_before_limit, p.limit.child_count, inf
        )
        is_eligible = (child_index != -1) & (
            child_index <= child_limit_applying
        )

        # Reform proposal
        age_exemption = parameters.gov.contrib.two_child_limit.age_exemption.universal_credit(
            period
        )
        if age_exemption > 0:
            is_exempt = person.benunit.any(
                person("age", period) < age_exemption
            )
            born_before_limit = is_exempt

        return (
            select(
                [
                    (child_index == 1) & born_before_limit & is_eligible,
                    is_eligible,
                ],
                [
                    p.first.higher_amount,
                    p.amount,
                ],
                default=0,
            )
            * MONTHS_IN_YEAR
        )

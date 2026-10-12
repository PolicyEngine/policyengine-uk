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
        uc_child_index = person("uc_child_index", period)
        born_before_limit = person("uc_is_child_born_before_child_limit", period)
        exempt_from_limit = born_before_limit

        # Reform proposal: a benefit unit with any member under the age
        # threshold is exempt from the two-child limit. The exemption lifts the
        # limit only; the higher first-child amount still requires a birth
        # before the limit.
        age_exemption = (
            parameters.gov.contrib.two_child_limit.age_exemption.universal_credit(
                period
            )
        )
        if age_exemption > 0:
            is_exempt = person.benunit.any(person("age", period) < age_exemption)
            exempt_from_limit = exempt_from_limit | is_exempt

        child_limit_applying = where(exempt_from_limit, inf, p.limit.child_count)
        is_eligible = (uc_child_index != -1) & (uc_child_index <= child_limit_applying)

        return (
            select(
                [
                    (uc_child_index == 1) & born_before_limit & is_eligible,
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

from policyengine_uk.model_api import *


class is_CTC_child_element_included(Variable):
    value_type = bool
    entity = Person
    label = "Child Tax Credit individual element included for this child"
    documentation = (
        "Whether the maximum rate of Child Tax Credit includes an individual "
        "element for this child or qualifying young person under the child "
        "limit: they are exempt from it (born before 6 April 2017), they are "
        "within the limit in the order of children, or an exception applies."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/7/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/9/2025-04-06",
    )

    def formula(person, period, parameters):
        child_limit = parameters(
            period
        ).gov.dwp.tax_credits.child_tax_credit.limit.child_count
        is_ctc_child = person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        # Reg 7(2A) and reg 9(1): the first and second children in the reg
        # 9(5) order, and a third or later child with an exception.
        within_limit = person("ctc_child_limit_position", period) <= child_limit
        return is_ctc_child & (
            person("is_CTC_child_limit_exempt", period)
            | within_limit
            | person("is_CTC_child_limit_exception", period)
        )

from policyengine_uk.model_api import *


class is_CTC_child_limit_exception(Variable):
    value_type = bool
    entity = Person
    label = "Child Tax Credit child limit exception for a third or later child"
    documentation = (
        "Whether an exception to the Child Tax Credit child limit applies to "
        "this child or qualifying young person if they are the third or a "
        "later child: the multiple births, adoption, non-parental caring "
        "arrangements, non-consensual conception or continuation exception, "
        "or all, or all but one, of the other children being adopted or "
        "cared for under a non-parental caring arrangement."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/9/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/10/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/11/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/12/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/13/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/14/2025-04-06",
    )

    def formula(person, period, parameters):
        is_ctc_child = person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        adopted_or_cared_for = person(
            "child_limit_adoption_exception", period
        ) | person("child_limit_non_parental_caring_exception", period)
        # Reg 9(1)(a)(i): regulations 10 to 14.
        own_exception = (
            adopted_or_cared_for
            | person("child_limit_multiple_birth_exception", period)
            | person("child_limit_non_consensual_conception_exception", period)
            | person("child_limit_continuation_exception", period)
        )
        # Reg 9(1)(a)(ii): all, or all but one, of the other children are
        # adopted (reg 11) or under a non-parental caring arrangement
        # (reg 12).
        other_children = person.benunit.sum(is_ctc_child) - is_ctc_child
        other_adopted_or_cared_for = person.benunit.sum(
            is_ctc_child & adopted_or_cared_for
        ) - (is_ctc_child & adopted_or_cared_for)
        others_adopted_or_cared_for = other_adopted_or_cared_for >= other_children - 1
        return is_ctc_child & (own_exception | others_adopted_or_cared_for)

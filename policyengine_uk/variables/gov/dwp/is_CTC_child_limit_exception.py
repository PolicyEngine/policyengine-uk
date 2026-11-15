from policyengine_uk.model_api import *


class is_CTC_child_limit_exception(Variable):
    value_type = bool
    entity = Person
    label = "Child Tax Credit child limit exception for a third or later child"
    documentation = (
        "Whether an exception to the Child Tax Credit child limit applies to "
        "this third or later child or qualifying young person: the multiple "
        "births, adoption, non-parental caring arrangements, non-consensual "
        "conception or continuation exception, or all, or all but one, of "
        "the other children being adopted or cared for under a non-parental "
        "caring arrangement (from 28 November 2018)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/9/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/10/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/11/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/12/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/13/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/14/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2018/1130/regulation/3/made",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.tax_credits.child_tax_credit.limit
        is_ctc_child = person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        # Reg 9(1)(a)(i): regulations 10 to 14.
        own_exception = person("is_CTC_child_limit_own_exception", period)
        # Reg 9(1)(a)(ii), in force from 28 November 2018 (SI 2018/1130):
        # all, or all but one, of the other children are adopted (reg 11)
        # or under a non-parental caring arrangement (reg 12).
        adopted_or_cared_for = person(
            "child_limit_adoption_exception", period
        ) | person("child_limit_non_parental_caring_exception", period)
        other_children = person.benunit.sum(is_ctc_child) - is_ctc_child
        other_adopted_or_cared_for = person.benunit.sum(
            is_ctc_child & adopted_or_cared_for
        ) - (is_ctc_child & adopted_or_cared_for)
        others_adopted_or_cared_for = (
            other_adopted_or_cared_for >= other_children - 1
        ) & bool(p.other_children_adopted_or_cared_for_exception)
        # Reg 9(1)(a) is for a third or later child in the reg 9(5) order;
        # reg 9(1)(b) covers the first and second.
        beyond_limit = person("ctc_child_limit_position", period) > p.child_count
        return (
            is_ctc_child & beyond_limit & (own_exception | others_adopted_or_cared_for)
        )

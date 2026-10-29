from policyengine_uk.model_api import *


class uc_child_limit_exception(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit child limit exception for a third or later child"
    documentation = (
        "Whether the child element is available for this child or qualifying "
        "young person even when they are the third or a later child in the "
        "household's order, because the multiple births, non-consensual "
        "conception or continuation exception applies, or, before 28 "
        "November 2018, the adoption or non-parental caring arrangements "
        "exception."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/24A/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/12/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/24A/2018-11-27",
    )

    def formula(person, period, parameters):
        # Reg 24A(1)(b)(ii): Schedule 12 paragraphs 2, 5 and 6.
        exception = (
            person("child_limit_multiple_birth_exception", period)
            | person("child_limit_non_consensual_conception_exception", period)
            | person("child_limit_continuation_exception", period)
        )
        # Before 28 November 2018 reg 24A(1)(b)(ii) covered every Schedule
        # 12 exception, so an adopted child or one in non-parental care
        # kept their place in the order and got the element as a third or
        # later child (SI 2018/1129 reg 3(3)).
        outside_order = parameters(
            period
        ).gov.dwp.universal_credit.elements.child.limit.adoption_and_kinship_outside_order
        if not outside_order:
            exception = (
                exception
                | person("child_limit_adoption_exception", period)
                | person("child_limit_non_parental_caring_exception", period)
            )
        return exception

from policyengine_uk.model_api import *


class uc_child_limit_exception(Variable):
    value_type = bool
    entity = Person
    label = "Universal Credit child limit exception for a third or later child"
    documentation = (
        "Whether the child element is available for this child or qualifying "
        "young person even when they are the third or a later child in the "
        "household's order, because the multiple births, non-consensual "
        "conception or continuation exception applies."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/24A/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/12/2025-04-06",
    )

    def formula(person, period, parameters):
        # Reg 24A(1)(b)(ii): Schedule 12 paragraphs 2, 5 and 6.
        return (
            person("child_limit_multiple_birth_exception", period)
            | person("child_limit_non_consensual_conception_exception", period)
            | person("child_limit_continuation_exception", period)
        )

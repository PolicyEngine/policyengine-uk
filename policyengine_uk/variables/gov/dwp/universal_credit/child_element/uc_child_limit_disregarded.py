from policyengine_uk.model_api import *


class uc_child_limit_disregarded(Variable):
    value_type = bool
    entity = Person
    label = "Disregarded from the Universal Credit child limit"
    documentation = (
        "Whether the child element is available for this child or qualifying "
        "young person whatever their place in the household, and they are "
        "left out of the order of children that the limit counts, because "
        "the adoption or non-parental caring arrangements exception applies."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/24A/2025-04-06",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/24B/2025-04-06",
    )

    def formula(person, period, parameters):
        # Reg 24A(1)(za)(i) and reg 24B(2A). Reg 24A(1)(za)(ii), a
        # continuation under Schedule 12 paragraph 6 of an adoption
        # exception, is not distinguished from other continuations: see
        # child_limit_continuation_exception.
        is_uc_child = person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        ) & ~person("is_uc_claimant", period)
        return is_uc_child & (
            person("child_limit_adoption_exception", period)
            | person("child_limit_non_parental_caring_exception", period)
        )

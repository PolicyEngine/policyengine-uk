from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_day


class uc_child_limit_position(Variable):
    value_type = int
    entity = Person
    label = "Position in the order of children for the Universal Credit child limit"
    documentation = (
        "This child or qualifying young person's place in the order of "
        "children that the Universal Credit child limit counts, 1 for the "
        "eldest, or -1 for anyone left out of the order: adults, claimants, "
        "and children the adoption or non-parental caring arrangements "
        "exception applies to."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/24B/2025-04-06"

    def formula(person, period, parameters):
        is_uc_child = person(
            "is_child_or_qualifying_young_person_for_universal_credit", period
        ) & ~person("is_uc_claimant", period)
        # Reg 24B(2A): children under reg 24A(1)(za) are disregarded.
        in_order = is_uc_child & ~person("uc_child_limit_disregarded", period)
        # Reg 24B(1) orders by date of birth, earliest first. Reg 24B(2)
        # orders children born on the same day so that the child element is
        # available for as many as possible, so a child with the multiple
        # births exception comes after a sibling born that day without it.
        multiple_birth = person("child_limit_multiple_birth_exception", period)
        order_key = birth_day(person, period) + 0.5 * multiple_birth
        rank = person.get_rank(person.benunit, order_key, condition=in_order) + 1
        return where(in_order, rank, -1)

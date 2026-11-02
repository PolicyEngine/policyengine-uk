from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_day


class ctc_child_limit_position(Variable):
    value_type = int
    entity = Person
    label = "Position in the order of children for the Child Tax Credit child limit"
    documentation = (
        "This child or qualifying young person's place in the order of "
        "children that the Child Tax Credit child limit counts, 1 for the "
        "first, or -1 for anyone who is not a child or qualifying young "
        "person for Child Tax Credit."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/regulation/9/2025-04-06"

    def formula(person, period, parameters):
        is_ctc_child = person(
            "is_child_or_qualifying_young_person_for_child_tax_credit", period
        )
        # Reg 9(5) orders children by date of birth where a claimant is the
        # parent or step-parent other than by adoption, and otherwise by the
        # date a claimant became responsible for them, which the model does
        # not hold, so it orders every child by date of birth. Reg 9(6)
        # orders children with the same date so that the individual element
        # is included for as many as possible. A child with their own
        # exception under regs 10 to 14 gets the element in any place, so
        # every child with that date and one comes after those without,
        # whatever the exception.
        exception = person("is_CTC_child_limit_own_exception", period)
        order_key = birth_day(person, period) + 0.5 * exception
        rank = person.get_rank(person.benunit, order_key, condition=is_ctc_child) + 1
        return where(is_ctc_child, rank, -1)

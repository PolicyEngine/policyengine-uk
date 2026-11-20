from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.overlapping_state_pension import (
    state_pension_overlapping_part,
)


class carer_support_payment_overlapping_state_pension(Variable):
    value_type = float
    entity = Person
    label = "State Pension that overlaps with Carer Support Payment"
    documentation = (
        "The State Pension by which Carer Support Payment is reduced. A new "
        "State Pension overlaps in full, including any protected payment above "
        "the full rate. An old State Pension (a Retirement Pension) overlaps "
        "without its additional pension but with its age addition: the "
        "regulations exclude only additional pension and graduated retirement "
        "benefit. The model's reported-total split and input convention are "
        "those of overlapping_state_pension."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ssi/2023/302/regulation/16"

    def formula(person, period, parameters):
        # SSI 2023/302 reg 16(3)(a) lists "State Pension or Retirement
        # Pension", and reg 16(6) defines Retirement Pension as "a pension
        # payable under Part II and Part III of the 1992 Act, excluding any
        # additional pension or graduated retirement benefit". The age
        # addition is in Part III (SSCBA 1992 s.79) and is not excluded, so,
        # unlike for Carer's Allowance (SI 1979/597 reg 4(3)), it overlaps.
        return state_pension_overlapping_part(
            person, period, age_addition_overlaps=True
        )

from policyengine_uk.model_api import *


class is_before_first_september_after_16th_birthday(Variable):
    value_type = bool
    entity = Person
    label = "Before the 1 September following their 16th birthday"
    documentation = (
        "Whether this person has reached 16 and it is not yet the 1 September "
        "following their 16th birthday. Until that date a 16-year-old is a "
        "qualifying young person for Pension Credit with no education or "
        "training condition (SPC Regs 2002 reg 4A(1)(a)). The annual model holds "
        "age in whole years and no date of birth, so this is an input. It "
        "defaults to false. It matters only for a 16-year-old who is not in "
        "non-advanced education or approved training: one who is qualifies "
        "under reg 4A(1)(b) without it."
    )
    definition_period = YEAR
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/4A"

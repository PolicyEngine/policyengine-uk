from policyengine_uk.model_api import *


class would_receive_aa_or_dla_care_but_for_hospital_stay(Variable):
    value_type = bool
    entity = Person
    label = "Would receive Attendance Allowance or DLA care but for a hospital stay"
    documentation = (
        "Whether this person would be in receipt of Attendance Allowance or "
        "the Disability Living Allowance care component at the highest or "
        "middle rate but for being a hospital patient for more than 28 days. "
        "SPC Regs 2002 Sch. I para. 1(2)(b) treats such a partner as in "
        "receipt for the couple test in para. 1(1)(b), and reg. 6(5)(b) then "
        "withholds the double rate."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6",
    )

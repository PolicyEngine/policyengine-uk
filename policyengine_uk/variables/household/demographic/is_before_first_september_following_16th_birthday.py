from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_day


class is_before_first_september_following_16th_birthday(Variable):
    value_type = bool
    entity = Person
    label = (
        "Before the 1 September following the 16th birthday at the start of the year"
    )
    documentation = (
        "Whether the fiscal year starts (6 April) before the 1 September "
        "following the person's 16th birthday, so that some of the year falls "
        "in the qualifying young person route that has no education condition "
        "(UC Regs 2013 reg. 5(1)(a); SPC Regs 2002 reg. 4A(1)(a)). The date "
        "comes from date_of_birth, or from age and months_since_last_birthday. "
        "A 16th birthday on 31 August ends the route that day, and one on 1 "
        "September runs it to the 17th birthday. The route ends on a fixed 1 "
        "September that annual periods cannot split, so a person in it for "
        "part of the year counts for the year, as the benefit cap and LHA "
        "family rules count a 16-year-old member. This departs from the 6 "
        "October reading of annual status that is_SP_age uses. Everyone aged "
        "16 on 6 October qualifies, as does a 17-year-old born from 1 "
        "September to 6 October. With birthdays spread evenly, a 16-year-old "
        "outside education is a child or in the route for 46% of the year on "
        "average, and a 17-year-old for 4%. To place the route for one "
        "person, set their date_of_birth. Setting this variable for some "
        "people gives everyone else in the situation false, so set it for "
        "every person or not at all."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/4A",
    )

    def formula(person, period, parameters):
        date_of_birth = birth_day(person, period)
        # The 16th birthday falls in the birth year plus 16; the 1 September
        # following it is in that year if the birthday is before 1 September,
        # and otherwise in the next.
        born_on_or_after_first_september = date_of_birth % 10_000 >= 901
        year_of_first_september = (
            date_of_birth // 10_000 + 16 + born_on_or_after_first_september
        )
        # The year starts on 6 April, before 1 September of the same calendar
        # year and after 1 September of the one before.
        return year_of_first_september >= period.start.year

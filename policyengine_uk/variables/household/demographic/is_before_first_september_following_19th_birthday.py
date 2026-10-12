from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_day


class is_before_first_september_following_19th_birthday(Variable):
    value_type = bool
    entity = Person
    label = (
        "Before the 1 September following the 19th birthday at the start of the year"
    )
    documentation = (
        "Whether the fiscal year starts (6 April) before the 1 September "
        "following the person's 19th birthday, the date to which a young "
        "person in non-advanced education or approved training stays a "
        "qualifying young person (UC Regs 2013 reg. 5(1)(b); SPC Regs 2002 "
        "reg. 4A(1)(b)). The date comes from date_of_birth, or from age and "
        "months_since_last_birthday. A 19th birthday on 31 August ends the "
        "period that day, and one on 1 September runs it to the 20th "
        "birthday. The period ends on a fixed 1 September that annual "
        "periods cannot split, so a person in it for part of the year counts "
        "for the year, as is_before_first_september_following_16th_birthday "
        "does. Everyone aged 19 on 6 October is before the date. So is a "
        "20-year-old born from 1 September to 6 October, whom the qualifying "
        "young person age limit, read on 6 October, already excludes. So the "
        "formula gives true for everyone under 20 on 6 October, which is "
        "everyone that limit lets be a qualifying young person, and the "
        "default is true: a situation that sets this for some people gives "
        "everyone else true, the value the formula gives them. Set it to "
        "false for a person whose 1 September has passed, or set their "
        "date_of_birth."
    )
    definition_period = YEAR
    default_value = True
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/4A",
    )

    def formula(person, period, parameters):
        date_of_birth = birth_day(person, period)
        # The 19th birthday falls in the birth year plus 19; the 1 September
        # following it is in that year if the birthday is before 1 September,
        # and otherwise in the next.
        born_on_or_after_first_september = date_of_birth % 10_000 >= 901
        year_of_first_september = (
            date_of_birth // 10_000 + 19 + born_on_or_after_first_september
        )
        # The year starts on 6 April, before 1 September of the same calendar
        # year and after 1 September of the one before.
        return year_of_first_september >= period.start.year

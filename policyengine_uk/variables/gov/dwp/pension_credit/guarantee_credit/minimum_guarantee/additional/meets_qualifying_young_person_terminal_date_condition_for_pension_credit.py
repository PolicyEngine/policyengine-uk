from policyengine_uk.model_api import *


class meets_qualifying_young_person_terminal_date_condition_for_pension_credit(
    Variable
):
    value_type = bool
    entity = Person
    label = "Meets qualifying young person terminal date condition for Pension Credit"
    documentation = (
        "A young person in education or training is a qualifying young person "
        "up to, but not including, the 1 September following their 19th "
        "birthday (SPC Regs 2002 reg. 4A(1)(b)). Under 19 that date is always "
        "ahead; at 19 it is read from "
        "is_before_first_september_following_19th_birthday. Its default is "
        "true, the value the formula gives everyone under 20 on 6 October, so "
        "setting it for some people leaves everyone else under 20 where the "
        "formula puts them; older people are excluded by the age limit."
    )
    definition_period = YEAR
    default_value = True
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/4A"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.guarantee_credit.child.eligibility
        age = person("age", period)
        return (age < p.terminal_date_age_limit) | person(
            "is_before_first_september_following_19th_birthday", period
        )

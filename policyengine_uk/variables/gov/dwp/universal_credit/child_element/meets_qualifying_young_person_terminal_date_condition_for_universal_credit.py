from policyengine_uk.model_api import *


class meets_qualifying_young_person_terminal_date_condition_for_universal_credit(
    Variable
):
    value_type = bool
    entity = Person
    label = "Meets qualifying young person terminal date condition for Universal Credit"
    documentation = (
        "A young person in education or training is a qualifying young person "
        "up to, but not including, the 1 September following their 19th "
        "birthday (UC Regs 2013 reg. 5(1)(b)). Under 19 that date is always "
        "ahead; at 19 it is read from "
        "is_before_universal_credit_qualifying_young_person_terminal_date, "
        "which follows the date of birth unless set."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.gov.uk/government/publications/universal-credit-and-families-with-more-than-2-children-information-for-stakeholders/universal-credit-and-families-with-more-than-2-children-information-for-stakeholders",
    )

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.child.eligibility
        age = person("age", period)
        return (age < p.terminal_date_age_limit) | person(
            "is_before_universal_credit_qualifying_young_person_terminal_date",
            period,
        )

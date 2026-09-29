from policyengine_uk.model_api import *


class meets_qualifying_young_person_terminal_date_condition_for_pension_credit(
    Variable
):
    value_type = bool
    entity = Person
    label = "Meets qualifying young person terminal date condition for Pension Credit"
    documentation = (
        "A qualifying young person in education or training counts only up to, "
        "but not including, the 1 September following their 19th birthday. "
        "Before age 19 that date is always in the future."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/4A"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.guarantee_credit.child.eligibility
        age = person("age", period)
        return (age < p.terminal_date_age_limit) | person(
            "is_before_first_september_after_19th_birthday", period
        )

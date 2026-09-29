from policyengine_uk.model_api import *


class meets_qualifying_young_person_terminal_date_condition_for_universal_credit(
    Variable
):
    value_type = bool
    entity = Person
    label = "Meets qualifying young person terminal date condition for Universal Credit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/5"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.child.eligibility
        age = person("age", period)
        return (age < p.terminal_date_age_limit) | person(
            "is_before_first_september_after_19th_birthday",
            period,
        )

from policyengine_uk.model_api import *


class meets_qualifying_young_person_terminal_date_condition_for_universal_credit(
    Variable
):
    value_type = bool
    entity = Person
    label = "Meets qualifying young person terminal date condition for Universal Credit"
    definition_period = YEAR
    reference = "https://www.gov.uk/government/publications/universal-credit-and-families-with-more-than-2-children-information-for-stakeholders/universal-credit-and-families-with-more-than-2-children-information-for-stakeholders"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.child.eligibility
        age = person("age", period)
        return (age < p.terminal_date_age_limit) | person(
            "is_before_universal_credit_qualifying_young_person_terminal_date",
            period,
        )

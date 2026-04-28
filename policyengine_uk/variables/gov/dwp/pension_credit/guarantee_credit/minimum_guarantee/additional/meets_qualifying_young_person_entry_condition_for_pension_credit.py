from policyengine_uk.model_api import *


class meets_qualifying_young_person_entry_condition_for_pension_credit(Variable):
    value_type = bool
    entity = Person
    label = "Meets qualifying young person entry condition for Pension Credit"
    definition_period = YEAR
    reference = "https://www.gov.uk/government/publications/pension-credit-technical-guidance/a-detailed-guide-to-pension-credit-for-advisers-and-others"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.guarantee_credit.child.eligibility
        age = person("age", period)
        entry_age = person(
            "age_started_or_accepted_current_education_or_training", period
        )
        return (age < p.education_or_training_start_age_limit) | (
            entry_age < p.education_or_training_start_age_limit
        )

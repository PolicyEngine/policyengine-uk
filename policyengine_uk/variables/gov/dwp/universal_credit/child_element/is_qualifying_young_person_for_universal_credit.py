from policyengine_uk.model_api import *


class is_qualifying_young_person_for_universal_credit(Variable):
    value_type = bool
    entity = Person
    label = "Qualifying young person for Universal Credit"
    documentation = (
        "A person aged 16 to 19 who is either before the 1 September following "
        "their 16th birthday, whatever their education (reg. 5(1)(a)), or in "
        "non-advanced education or approved training that meets the entry and "
        "terminal-date conditions (reg. 5(1)(b), (2) and (3)), and who is not "
        "receiving Universal Credit, Employment and Support Allowance or "
        "Jobseeker's Allowance (reg. 5(5))."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/5"

    def formula(person, period, parameters):
        # Reg. 5(1)(a): no education or training condition.
        before_first_september_following_16th_birthday = person(
            "is_before_first_september_following_16th_birthday", period
        )
        # Reg. 5(1)(b), (2) and (3).
        in_education_or_training = (
            person(
                "meets_qualifying_young_person_education_or_training_condition_for_universal_credit",
                period,
            )
            & person(
                "meets_qualifying_young_person_entry_condition_for_universal_credit",
                period,
            )
            & person(
                "meets_qualifying_young_person_terminal_date_condition_for_universal_credit",
                period,
            )
        )
        return (
            person(
                "meets_qualifying_young_person_age_condition_for_universal_credit",
                period,
            )
            & (
                before_first_september_following_16th_birthday
                | in_education_or_training
            )
            & ~person("receives_benefits_in_own_right", period)
        )

from policyengine_uk.model_api import *


class is_qualifying_young_person_for_pension_credit(Variable):
    value_type = bool
    entity = Person
    label = "Qualifying young person for Pension Credit"
    documentation = (
        "A person aged 16 to 19 is a qualifying young person (a) until the 1 "
        "September following their 16th birthday, with no education condition, "
        "and (b) until the 1 September following their 19th birthday while in "
        "non-advanced education or approved training begun before 19. Nobody "
        "receiving Universal Credit, Employment and Support Allowance, "
        "Jobseeker's Allowance or Income Support counts."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/4A"

    def formula(person, period, parameters):
        # Reg 4A(1)(a): every 16-year-old until the 1 September after their
        # 16th birthday.
        before_september_after_16th_birthday = person(
            "is_before_first_september_after_16th_birthday", period
        )
        # Reg 4A(1)(b), (2): education or training begun before 19, until the
        # 1 September after their 19th birthday.
        in_education_or_training = (
            person(
                "meets_qualifying_young_person_education_or_training_condition_for_pension_credit",
                period,
            )
            & person(
                "meets_qualifying_young_person_entry_condition_for_pension_credit",
                period,
            )
            & person(
                "meets_qualifying_young_person_terminal_date_condition_for_pension_credit",
                period,
            )
        )
        return (
            person(
                "meets_qualifying_young_person_age_condition_for_pension_credit",
                period,
            )
            & (before_september_after_16th_birthday | in_education_or_training)
            # Reg 4A(5).
            & ~person("receives_benefits_in_own_right", period)
        )

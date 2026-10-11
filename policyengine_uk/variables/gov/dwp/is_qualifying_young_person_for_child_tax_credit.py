from policyengine_uk.model_api import *


class is_qualifying_young_person_for_child_tax_credit(Variable):
    value_type = bool
    entity = Person
    label = "Qualifying young person for Child Tax Credit"
    documentation = (
        "A person aged 16 to 19 who meets the Child Tax Credit Regulations "
        "2002's conditions. The first condition (reg. 5(3)) is full-time "
        "non-advanced education or approved training, begun before 19, or, "
        "under 18, the 20 weeks after leaving while registered for work or "
        "training. Reg. 4(1) lifts the first condition from the 16th "
        "birthday until the 31 August that next follows it. That period "
        "reads is_before_first_september_following_16th_birthday, so it "
        "counts in any year that starts before the 31 August. For a 16th "
        "birthday on 31 August, reg. 4(1A) gives no such period, where "
        "Universal Credit gives that day and Child Benefit two: the year "
        "counts all the same, as the one in which the person is a child "
        "until 30 August, and not the year after. The second condition "
        "(reg. 5(4)) always applies: a young person who has left education or "
        "training must not be in remunerative work, and no one may be "
        "receiving a benefit in their own right. That is read from the "
        "own-right inputs for Universal Credit, Employment and Support "
        "Allowance, Jobseeker's Allowance and Income Support; reg. 5(4)(c) "
        "lists Universal Credit, Income Support and only the income-related "
        "and income-based allowances, which the inputs do not separate. "
        "Interruptions (reg. 5(7)) are not modelled."
    )
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/4",
        "https://www.legislation.gov.uk/uksi/2002/2007/regulation/5",
    ]

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.tax_credits.child_tax_credit.eligibility
        # Reg. 5(3)(a), (ab) and (3A).
        receiving_education_or_training = person(
            "meets_qualifying_young_person_education_or_training_condition_for_child_tax_credit",
            period,
        )
        in_education_or_training = receiving_education_or_training & person(
            "meets_qualifying_young_person_entry_condition_for_child_tax_credit",
            period,
        )
        # Reg. 4(1): from the 16th birthday to the 31 August that next
        # follows.
        before_31_august_following_16th_birthday = person(
            "is_before_first_september_following_16th_birthday", period
        )
        # Reg. 5(3)(b): 20 weeks after leaving, under 18.
        in_extension_period = (
            person("age", period) < p.extension_period_age_limit
        ) & person("is_in_child_tax_credit_extension_period", period)
        # Reg. 5(4)(a): having left, not in remunerative work.
        left_and_not_working = ~receiving_education_or_training & ~person(
            "is_in_remunerative_work_for_child_tax_credit", period
        )
        return (
            person(
                "meets_qualifying_young_person_age_condition_for_child_tax_credit",
                period,
            )
            & (
                in_education_or_training
                | (
                    (before_31_august_following_16th_birthday | in_extension_period)
                    & left_and_not_working
                )
            )
            # Reg. 5(4)(c).
            & ~person("receives_benefits_in_own_right", period)
            & ~person("receives_income_support_in_own_right", period)
        )

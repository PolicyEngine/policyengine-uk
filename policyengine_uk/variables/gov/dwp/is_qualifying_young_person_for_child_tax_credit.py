from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)


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
        "(reg. 5(4)) always applies: a young person who has ceased full-time "
        "education or approved training must not be in remunerative work, and "
        "no one may be receiving a benefit in their own right. Full-time "
        "education at any level counts (reg. 5(5)), so an advanced student "
        "has not ceased it, nor has an apprentice still on a course; the "
        "employment exclusion is part of the first condition only. The "
        "own-right benefits are read from the inputs for Universal Credit, "
        "Employment and Support Allowance, Jobseeker's Allowance and Income "
        "Support; reg. 5(4)(c) lists Universal Credit, Income Support and "
        "only the income-related and income-based allowances, which the "
        "inputs do not separate. "
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
        # Reg. 5(4)(a) bars remunerative work only for a person "having
        # ceased to receive full-time education or approved training".
        # Full-time education at a school or college counts at any level
        # (reg. 5(5)), so failing the non-advanced test of reg. 5(3)(a) does
        # not mean having ceased it.
        # Education received by virtue of employment is left out of the first
        # condition (reg. 5(3)(a)), which reg. 4(2) lifts, and not out of reg.
        # 5(5): an apprentice still on a course has not ceased it.
        in_full_time_education = (
            person("current_education", period) != EducationType.NOT_IN_EDUCATION
        )
        ceased = ~in_full_time_education & ~person("is_in_approved_training", period)
        working = person("is_in_remunerative_work_for_child_tax_credit", period)
        # Reg. 4(2): the period needs no first condition, only the second.
        in_regulation_4_period = before_31_august_following_16th_birthday & ~(
            ceased & working
        )
        # Reg. 5(3)(b) is for a person who has ceased.
        in_20_weeks = in_extension_period & ceased & ~working
        return (
            person(
                "meets_qualifying_young_person_age_condition_for_child_tax_credit",
                period,
            )
            & (in_education_or_training | in_regulation_4_period | in_20_weeks)
            # Reg. 5(4)(c).
            & ~person("receives_benefits_in_own_right", period)
            & ~person("receives_income_support_in_own_right", period)
        )

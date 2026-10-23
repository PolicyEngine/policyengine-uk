from policyengine_uk.model_api import *


class is_qualifying_young_person_for_child_benefit(Variable):
    value_type = bool
    entity = Person
    label = "Qualifying young person for Child Benefit"
    documentation = (
        "A person aged 16 to 19 who meets any of the conditions in Child "
        "Benefit (General) Regulations 2006 regs 3 to 7 (reg. 2(2): a "
        "qualifying young person until the last of them ceases to be met) "
        "and is not receiving a benefit in their own right (reg. 8). The "
        "conditions modelled are: non-advanced education or approved "
        "training, begun before 19 (reg. 3); the period to the 31 August "
        "after the 16th birthday, whatever their education (reg. 4); an "
        "extension period for a 16- or 17-year-old (reg. 5); and the period "
        "to the terminal date after leaving education (reg. 7). Reg. 4 "
        "reads is_before_first_september_following_16th_birthday: its 31 "
        "August (1 September for a 16th birthday on 31 August) falls in the "
        "same fiscal year as Universal Credit's 1 September, so a year that "
        "starts before one starts before the other. Interruptions (reg. 6) "
        "are not modelled. The own-right benefits input covers Universal "
        "Credit, Employment and Support Allowance and Jobseeker's Allowance "
        "but not the Income Support, incapacity benefit and tax credits that "
        "reg. 8 also lists."
    )
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/ukpga/1992/4/section/142",
        "https://www.legislation.gov.uk/uksi/2006/223/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/223/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/223/regulation/4",
        "https://www.legislation.gov.uk/uksi/2006/223/regulation/5",
        "https://www.legislation.gov.uk/uksi/2006/223/regulation/7",
        "https://www.legislation.gov.uk/uksi/2006/223/regulation/8",
    ]

    def formula(person, period, parameters):
        # Reg. 3: education or training, begun before 19.
        in_education_or_training = person(
            "meets_qualifying_young_person_education_or_training_condition_for_child_benefit",
            period,
        ) & person(
            "meets_qualifying_young_person_entry_condition_for_child_benefit",
            period,
        )
        # Reg. 4: until the 31 August after the 16th birthday. A person in
        # that period is under 17, as reg. 4(1) requires.
        before_31_august_following_16th_birthday = person(
            "is_before_first_september_following_16th_birthday", period
        )
        # Reg. 5: the extension period.
        in_extension_period = person(
            "meets_qualifying_young_person_extension_period_condition_for_child_benefit",
            period,
        )
        # Reg. 7: until the terminal date after leaving.
        before_terminal_date = person("is_before_child_benefit_terminal_date", period)
        return (
            person(
                "meets_qualifying_young_person_age_condition_for_child_benefit",
                period,
            )
            & (
                in_education_or_training
                | before_31_august_following_16th_birthday
                | in_extension_period
                | before_terminal_date
            )
            & ~person("receives_benefits_in_own_right", period)
        )

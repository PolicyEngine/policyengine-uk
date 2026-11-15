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
        "are not modelled. Reg. 8 reads the own-right benefits input, which "
        "covers Universal Credit, Employment and Support Allowance and "
        "Jobseeker's Allowance, the person's own reported Universal "
        "Credit, Employment and Support Allowance of either kind and "
        "income-based Jobseeker's Allowance, the awards reg. 8(2)(b), (e) "
        "and (f) list, and receives_income_support_in_own_right (reg. "
        "8(2)(a)). It does not read the incapacity benefit and tax credits "
        "that reg. 8 also lists. A positive report for the year ends the "
        "status for the whole year."
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
        # Reg. 8(2)(b), (e) and (f): income-based JSA, ESA and Universal
        # Credit. Reports are inputs, so reading them makes no cycle.
        receives_own_benefits = (
            person("receives_benefits_in_own_right", period)
            | (person("universal_credit_reported", period) > 0)
            | (person("esa_income_reported", period) > 0)
            | (person("esa_contrib_reported", period) > 0)
            | (person("jsa_income_reported", period) > 0)
        )
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
            & ~receives_own_benefits
            # Reg. 8(2)(a). The reported award, not is_on_income_support:
            # the family's Income Support reads this test, so the calculated
            # award would make a cycle.
            & ~person("receives_income_support_in_own_right", period)
        )

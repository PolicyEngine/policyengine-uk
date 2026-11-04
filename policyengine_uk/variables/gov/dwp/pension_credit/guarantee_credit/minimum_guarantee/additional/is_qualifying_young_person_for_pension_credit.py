from policyengine_uk.model_api import *


class is_qualifying_young_person_for_pension_credit(Variable):
    value_type = bool
    entity = Person
    label = "Qualifying young person for Pension Credit"
    documentation = (
        "A person aged 16 to 19 who is either before the 1 September following "
        "their 16th birthday, whatever their education (reg. 4A(1)(a)), or in "
        "non-advanced education or approved training that meets the entry "
        "condition (reg. 4A(1)(b), (2) and (3)), and who is not receiving "
        "Universal Credit, Employment and Support Allowance, Jobseeker's "
        "Allowance or Income Support in their own right (reg. 4A(5)). The "
        "own-right flag or their own reported award shows the first three; "
        "is_on_income_support shows Income Support. The model does not apply "
        "reg. 4A(1)(b)'s end at the 1 September after the 19th birthday."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/4A"

    def formula(person, period, parameters):
        # Reg. 4A(1)(a): no education or training condition.
        before_first_september_following_16th_birthday = person(
            "is_before_first_september_following_16th_birthday", period
        )
        # Reg. 4A(1)(b), (2) and (3).
        in_education_or_training = person(
            "meets_qualifying_young_person_education_or_training_condition_for_pension_credit",
            period,
        ) & person(
            "meets_qualifying_young_person_entry_condition_for_pension_credit",
            period,
        )
        # Reg. 4A(5) applies to both routes. Raw person-level reports identify
        # own awards without calculating family benefits, which depend on QYP
        # status and could recurse. Unlike UC reg. 5(5), it lists income
        # support, whose family follows the Child Benefit test and not this
        # one, so is_on_income_support can read the calculated award.
        receives_own_benefits = (
            person("receives_benefits_in_own_right", period)
            | (person("universal_credit_reported", period) > 0)
            | (person("esa_income_reported", period) > 0)
            | (person("esa_contrib_reported", period) > 0)
            | (person("jsa_income_reported", period) > 0)
            | (person("jsa_contrib_reported", period) > 0)
            | person("is_on_income_support", period)
        )
        return (
            person(
                "meets_qualifying_young_person_age_condition_for_pension_credit",
                period,
            )
            & (
                before_first_september_following_16th_birthday
                | in_education_or_training
            )
            & ~receives_own_benefits
        )

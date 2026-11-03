from policyengine_uk.model_api import *


class is_qualifying_young_person_under_universal_credit_regulation_5(Variable):
    value_type = bool
    entity = Person
    label = "Qualifying young person under Universal Credit Regulations reg. 5"
    documentation = (
        "A person aged 16 to 19 who is either before the 1 September following "
        "their 16th birthday, whatever their education (reg. 5(1)(a)), or in "
        "non-advanced education or approved training that meets the entry and "
        "terminal-date conditions (reg. 5(1)(b), (2) and (3)), and who receives "
        "no Universal Credit, contributory ESA or contribution-based JSA (reg. "
        "5(5)). The Secretary of State defines employment and support "
        "allowance and jobseeker's allowance without their income-related and "
        "income-based forms (UC Regs 2013 reg. 2), so this test leaves those to "
        "SI 2014/1230 reg. 28, which is_qualifying_young_person_for_universal_credit "
        "applies. Northern Ireland's twin is reg. 6 of the Universal Credit "
        "Regulations (Northern Ireland) 2016 (SR 2016/216). The Scottish "
        "Ministers define the young person for Scotland's working-age Council "
        "Tax Reduction by this regulation (SSI 2021/249 reg. 6(1))."
    )
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/2",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/nisr/2016/216/regulation/6",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/6",
    ]

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
        # The Secretary of State excludes a person receiving Universal Credit,
        # contributory ESA or contribution-based JSA (reg. 5(5)), on both
        # routes. The formula reads raw
        # person-level reports, so it calculates no family benefit that
        # depends on qualifying young person status.
        receives_reg_5_5_benefit = (
            person("receives_benefits_in_own_right", period)
            | (person("universal_credit_reported", period) > 0)
            | (person("esa_contrib_reported", period) > 0)
            | (person("jsa_contrib_reported", period) > 0)
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
            & ~receives_reg_5_5_benefit
        )

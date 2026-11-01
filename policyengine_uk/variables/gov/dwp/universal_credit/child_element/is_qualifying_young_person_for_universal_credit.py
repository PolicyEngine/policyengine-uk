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
        "Jobseeker's Allowance (reg. 5(5)), or an existing benefit: Income "
        "Support, Housing Benefit, Child Tax Credit or Working Tax Credit "
        "(Universal Credit (Transitional Provisions) Regulations 2014 reg. 28 "
        "and reg. 2(1)). The formula reads the person's own reported awards, "
        "and, for a claimant or partner, the couple's joint tax credit award "
        "(Tax Credits Act 2002 s.3(3))."
    )
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/28",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/2",
        "https://www.legislation.gov.uk/ukpga/2002/21/section/3",
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
        # Reg. 5(5) and Transitional Provisions reg. 28 exclude a person
        # receiving Universal Credit, any ESA or JSA, or an existing benefit
        # (TP reg. 2(1)), on both routes. Reg. 5(5) already covers
        # income-related ESA and income-based JSA. Raw person-level reports
        # identify own awards without calculating family benefits, which
        # depend on QYP status and could recurse. A dependant's own report
        # counts; a parent's report does not.
        tax_credits_reported = person("child_tax_credit_reported", period) + person(
            "working_tax_credit_reported", period
        )
        # Tax Credits Act 2002 s.3(3): the members of a couple claim jointly,
        # so the couple's award belongs to the claimant and the partner.
        claimant_or_partner = person("is_claimant_or_partner", period)
        couple_tax_credits_reported = person.benunit.sum(
            where(claimant_or_partner, tax_credits_reported, 0)
        )
        receives_tax_credits = (tax_credits_reported > 0) | (
            claimant_or_partner & (couple_tax_credits_reported > 0)
        )
        receives_own_benefits = (
            person("receives_benefits_in_own_right", period)
            | (person("universal_credit_reported", period) > 0)
            | (person("esa_income_reported", period) > 0)
            | (person("esa_contrib_reported", period) > 0)
            | (person("jsa_income_reported", period) > 0)
            | (person("jsa_contrib_reported", period) > 0)
            | (person("income_support_reported", period) > 0)
            | (person("housing_benefit_reported", period) > 0)
            | receives_tax_credits
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
            & ~receives_own_benefits
        )

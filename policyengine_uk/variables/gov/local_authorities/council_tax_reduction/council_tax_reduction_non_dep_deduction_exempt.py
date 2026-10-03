from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
    has_earned_income,
    is_award_payee,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_england_pensioner_scheme,
    is_scotland_scheme,
    is_wales_scheme,
)


class council_tax_reduction_non_dep_deduction_exempt(Variable):
    value_type = bool
    entity = Person
    label = "national Council Tax Reduction makes no non-dependant deduction for this person"
    documentation = (
        "Modelled exemptions in the England pensioner, Scottish and Welsh "
        "schemes: a full-time student; a non-dependant on Income Support, "
        "income-based JSA, income-related ESA or State Pension Credit (any "
        "age), and in Scotland's working-age scheme from April 2022 one whose "
        "partner is on Income Support, income-based JSA or income-related ESA "
        "and who is not on Universal Credit; an adult for whom someone else is "
        "entitled to child benefit (LGFA 1992 Sch 1 para 3); and, from the year "
        "each scheme added it, "
        "one entitled to Universal Credit calculated on no earned income. Wales excludes "
        "members of the ESA work-related activity group; with no ESA group "
        "input, income-related ESA is treated as exempt. Not modelled: other "
        "persons disregarded for council tax discounts (LGFA 1992 Sch 1), "
        "youth training allowances, a normal home elsewhere, and "
        "absence in hospital or on armed forces operations."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/6/paragraph/5",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/48",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/90",
        "https://www.legislation.gov.uk/ssi/2021/249/regulation/4",
        "https://www.legislation.gov.uk/ukpga/1992/14/schedule/1/paragraph/3",
    )

    def formula(person, period, parameters):
        local_authorities = parameters(period).gov.local_authorities
        england = local_authorities.england.council_tax_reduction.pensioners
        scotland = local_authorities.scotland.council_tax_reduction
        wales = local_authorities.wales.council_tax_reduction
        country = person.household("country", period)
        has_pensioner = person.household(
            "council_tax_reduction_household_has_pensioner", period
        )
        schemes = [
            is_england_pensioner_scheme(country, has_pensioner),
            is_scotland_scheme(country),
            is_wales_scheme(country),
        ]
        full_time_student = is_full_time_student_non_dep(person, period)
        # IS, income-based JSA, income-related ESA and SPC count for the person
        # they are payable to; Universal Credit for both joint claimants.
        claimant_or_partner = person("is_claimant_or_partner", period)
        on_legacy_income_related_benefit = (
            is_award_payee(person, period, "income_support", "income_support_reported")
            | is_award_payee(person, period, "jsa_income", "jsa_income_reported")
            | is_award_payee(person, period, "esa_income", "esa_income_reported")
        )
        on_pension_credit = is_award_payee(
            person, period, "pension_credit", "pension_credit_reported"
        )
        entitled_to_universal_credit = claimant_or_partner & (
            person.benunit("universal_credit_pre_benefit_cap", period) > 0
        )
        # SSI 2021/249 reg 90(8)(a): a "qualifying income-related benefit
        # claimant", defined in reg 4(1) as one "who is, or who has a partner
        # who is," on IS, income-based JSA or income-related ESA "and is not on
        # universal credit". Read for the non-dependant, as the definition's
        # "applicant" would leave the limb no application.
        couple_on_legacy_income_related_benefit = claimant_or_partner & (
            person.benunit.any(on_legacy_income_related_benefit & claimant_or_partner)
        )
        partner_rule = (
            is_scotland_scheme(country)
            & ~has_pensioner
            & scotland.non_dep_deduction.working_age_exempt_partner_of_income_related_benefit_claimant
        )
        qualifying_income_related_benefit_claimant = where(
            partner_rule,
            (on_legacy_income_related_benefit | couple_on_legacy_income_related_benefit)
            & ~entitled_to_universal_credit,
            on_legacy_income_related_benefit,
        )
        # LGFA 1992 Sch 1 para 3 (via para 8(8)(b) and equivalents): an adult
        # "in respect of whom another person is entitled to child benefit".
        # Entitlement needs a claim (SSAA 1992 s.1(1)); an election not to be
        # paid keeps it (s.13A), so the opt-out flag is not read.
        entitled_to_child_benefit_for = (
            add(person, period, ["child_benefit_respective_amount"]) > 0
        ) & person.benunit("would_claim_child_benefit", period)
        disregarded_for_child_benefit = (
            (person("age", period) >= 18)
            & entitled_to_child_benefit_for
            & ~claimant_or_partner
        )
        universal_credit_limb = select(
            schemes,
            [
                england.non_dep_deduction.exempt_universal_credit_without_earned_income,
                scotland.non_dep_deduction.exempt_universal_credit_without_earned_income,
                wales.non_dep_deduction.exempt_universal_credit_without_earned_income,
            ],
            default=False,
        )
        universal_credit_without_earned_income = (
            universal_credit_limb
            & entitled_to_universal_credit
            & ~has_earned_income(person, period)
        )
        return (
            full_time_student
            | qualifying_income_related_benefit_claimant
            | on_pension_credit
            | disregarded_for_child_benefit
            | universal_credit_without_earned_income
        )

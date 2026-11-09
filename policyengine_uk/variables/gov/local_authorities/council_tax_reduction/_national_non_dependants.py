"""National Council Tax Reduction non-dependant deductions under a given
applicant's scheme. Each applicant's scheme follows their own family
(council_tax_reduction_pensioner), so a person's deduction can differ between
two applicants in one household: England deducts under its pensioner scheme
only (working-age applicants are in the local schemes), Wales deducts for both
members of a Universal Credit couple only from a working-age applicant (WSI
2013/3029 Sch 6 para 5(3)), and Scotland's partner rule applies only in its
working-age scheme (SSI 2021/249 reg 90(8)(a))."""

from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
    has_earned_income,
    is_on_legacy_income_related_benefit,
    non_dependant_weekly_gross_income,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_england_pensioner_scheme,
    is_scotland_scheme,
    is_wales_scheme,
)


def household_head_family_is_pensioner(person, period):
    """The scheme of the household head's family, which the person-level
    variables report."""
    head_family = person.benunit("benunit_contains_household_head", period)
    pensioner = person.benunit("council_tax_reduction_pensioner", period)
    return person.household.any(head_family & pensioner)


def is_qualifying_income_related_benefit_claimant(
    person, period, parameters, pensioner_applicant
):
    """Whether the person is on Income Support, income-based JSA or
    income-related ESA for a scheme's non-dependant rules, under the claim of
    an applicant who is (pensioner_applicant) or is not a pensioner. Such a
    person is not in remunerative work (SI 2012/2885 reg 10(6); WSI 2013/3029
    reg 10(6); SSI 2012/319 reg 6(6); SSI 2021/249 reg 10(6)) and has no
    deduction (Sch 1 para 8(8)(a) and equivalents). In Scotland's working-age
    scheme from April 2022 this is a "qualifying income-related benefit
    claimant", defined in SSI 2021/249 reg 4(1) as one "who is, or who has a
    partner who is," on one of those benefits "and is not on universal
    credit". It is read for the non-dependant, as the definition's
    "applicant" would leave reg 90(8)(a) no application."""
    scotland = parameters(period).gov.local_authorities.scotland.council_tax_reduction
    country = person.household("country", period)
    claimant_or_partner = person("is_claimant_or_partner", period)
    on_benefit = is_on_legacy_income_related_benefit(person, period)
    couple_on_benefit = claimant_or_partner & (
        person.benunit.any(on_benefit & claimant_or_partner)
    )
    entitled_to_universal_credit = person("is_uc_assessed_claimant", period) & (
        person.benunit("universal_credit_pre_benefit_cap", period) > 0
    )
    partner_rule = (
        is_scotland_scheme(country)
        & ~pensioner_applicant
        & scotland.non_dep_deduction.working_age_exempt_partner_of_income_related_benefit_claimant
    )
    return where(
        partner_rule,
        (on_benefit | couple_on_benefit) & ~entitled_to_universal_credit,
        on_benefit,
    )


def non_dep_deduction_exempt(person, period, parameters, pensioner_applicant):
    """Whether a national scheme makes no deduction for this person from the
    claim of an applicant who is (pensioner_applicant) or is not a pensioner."""
    local_authorities = parameters(period).gov.local_authorities
    england = local_authorities.england.council_tax_reduction.pensioners
    scotland = local_authorities.scotland.council_tax_reduction
    wales = local_authorities.wales.council_tax_reduction
    country = person.household("country", period)
    schemes = [
        is_england_pensioner_scheme(country, pensioner_applicant),
        is_scotland_scheme(country),
        is_wales_scheme(country),
    ]
    full_time_student = is_full_time_student_non_dep(person, period)
    # IS, income-based JSA, income-related ESA and SPC count for the person
    # they are payable to; Universal Credit for both joint claimants.
    claimant_or_partner = person("is_claimant_or_partner", period)
    on_pension_credit = person("is_on_pension_credit", period)
    entitled_to_universal_credit = person("is_uc_assessed_claimant", period) & (
        person.benunit("universal_credit_pre_benefit_cap", period) > 0
    )
    qualifying_income_related_benefit_claimant = (
        is_qualifying_income_related_benefit_claimant(
            person, period, parameters, pensioner_applicant
        )
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


def individual_non_dep_deduction(person, period, parameters, pensioner_applicant):
    """A person's annual deduction from the claim of an applicant who is
    (pensioner_applicant) or is not a pensioner, before eligibility. Each
    scheme's own weekly scale; the band containing normal gross weekly income
    in remunerative work, bands including their lower edge ("not less than");
    the lowest amount otherwise (Sch 1 para 8(1)(b) and equivalents); nothing
    if exempt."""
    local_authorities = parameters(period).gov.local_authorities
    england = (
        local_authorities.england.council_tax_reduction.pensioners.non_dep_deduction
    )
    scotland = local_authorities.scotland.council_tax_reduction.non_dep_deduction
    wales = local_authorities.wales.council_tax_reduction.non_dep_deduction
    country = person.household("country", period)
    schemes = [
        is_england_pensioner_scheme(country, pensioner_applicant),
        is_scotland_scheme(country),
        is_wales_scheme(country),
    ]
    weekly_income = non_dependant_weekly_gross_income(
        person, period, parameters, "council_tax_reduction_non_dep_gross_income"
    )
    no_income = np.zeros_like(weekly_income)
    remunerative_work_hours = select(
        schemes,
        [
            england.remunerative_work_hours,
            scotland.remunerative_work_hours,
            wales.remunerative_work_hours,
        ],
        default=np.inf,
    )
    in_remunerative_work = (
        person("weekly_hours", period) >= remunerative_work_hours
    ) & ~is_qualifying_income_related_benefit_claimant(
        person, period, parameters, pensioner_applicant
    )
    banded = select(
        schemes,
        [
            england.amount.calc(weekly_income),
            scotland.amount.calc(weekly_income),
            wales.amount.calc(weekly_income),
        ],
        default=0,
    )
    not_in_remunerative_work = select(
        schemes,
        [
            england.amount.calc(no_income),
            scotland.amount.calc(no_income),
            wales.amount.calc(no_income),
        ],
        default=0,
    )
    weekly = where(in_remunerative_work, banded, not_in_remunerative_work)
    exempt = non_dep_deduction_exempt(person, period, parameters, pensioner_applicant)
    return where(exempt, 0, weekly * WEEKS_IN_YEAR)

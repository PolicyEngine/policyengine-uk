from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)


def is_full_time_student_non_dep(person, period):
    return (person("current_education", period) != EducationType.NOT_IN_EDUCATION) | (
        person("in_HE", period)
    )


def single_claim_is_pensioner(household, period):
    """Whether the household's single claim is a pensioner's.

    A non-dependant brings no deduction under a council's working-age scheme
    where the household's one claim is a pensioner's. Where families claim on
    their shares, each claim's own scheme decides whether its award uses the
    deduction (council_tax_reduction_claim_pensioner), so none is ruled out
    here.
    """
    return household(
        "council_tax_reduction_household_has_pensioner", period
    ) & ~household("council_tax_reduction_claims_are_joint", period)


def legacy_council_tax_reduction(
    benunit,
    period,
    ctr,
    working_age,
    non_dep_deductions_variable,
    additional_applicable_income=0,
):
    is_household_head_benunit = benunit(
        "council_tax_reduction_claimant_benunit", period
    )
    would_claim = benunit("would_claim_council_tax_reduction", period)
    applicable_amount = benunit("council_tax_reduction_applicable_amount", period)
    applicable_income = benunit("council_tax_reduction_applicable_income", period)
    universal_credit = benunit("universal_credit", period)
    has_uc_award = universal_credit > 0
    uc_applicable_amount = benunit("uc_maximum_amount", period)
    # The schemes use "the calculation or estimate of the amount of the
    # income of the applicant ... made by the Secretary of State for the
    # purpose of determining the award of universal credit", plus the award
    # (Default Scheme 2013 para. 37(1) and (3)(a); Kingston upon Thames and
    # Merton reproduce it, Newham refers to the same calculation, and
    # Westminster's scheme is based on the Default Scheme). That income is
    # earned income after tax, National Insurance and pension contributions
    # and unearned income. The work allowance and taper are steps in the
    # award (UC Regs 2013 reg. 22), not in the income, so the work allowance
    # is not deducted here.
    uc_applicable_income = (
        benunit("uc_earned_income_before_work_allowance", period)
        + benunit("uc_unearned_income", period)
        + universal_credit
    )
    applicable_amount = where(has_uc_award, uc_applicable_amount, applicable_amount)
    applicable_income = where(has_uc_award, uc_applicable_income, applicable_income)
    applicable_income += additional_applicable_income
    relevant_income_based_benefit = benunit(
        "council_tax_reduction_relevant_income_based_benefit",
        period,
    )
    liability = benunit.household(
        "council_tax_reduction_maximum_eligible_liability", period
    ) * benunit("council_tax_reduction_joint_liability_share", period)
    non_dep_deductions = benunit(non_dep_deductions_variable, period)
    excess_income = max_(0, applicable_income - applicable_amount)
    excess_income = where(
        relevant_income_based_benefit & ~has_uc_award, 0, excess_income
    )
    preliminary_award = max_(
        0,
        liability * ctr.maximum_support_rate
        - excess_income * ctr.means_test.withdrawal_rate
        - non_dep_deductions,
    )
    capital = where(
        has_uc_award,
        benunit("uc_assessable_capital", period),
        benunit.household("savings", period),
    )
    capital_eligible = capital <= ctr.means_test.capital_limit
    return (
        working_age
        * is_household_head_benunit
        * would_claim
        * capital_eligible
        * preliminary_award
    )


def local_non_dep_deductions(
    benunit,
    period,
    individual_deduction_variable,
    one_deduction_for_uc_couples=True,
):
    deductions = benunit.members(individual_deduction_variable, period)
    deduction_for_benunit = benunit.max(deductions)
    if not one_deduction_for_uc_couples:
        has_uc = benunit("universal_credit", period) > 0
        deduction_for_benunit = where(
            has_uc,
            benunit.sum(deductions),
            deduction_for_benunit,
        )
    is_benunit_head = benunit.members("is_benunit_head", period)
    deductions_to_count = is_benunit_head * benunit.project(deduction_for_benunit)
    deductions_in_household = benunit.max(
        benunit.members.household.sum(deductions_to_count)
    )
    # A non-dependant of two or more jointly liable people is apportioned
    # equally between them (SI 2012/2885 Sch 1 para 8(5)).
    share = benunit("council_tax_reduction_joint_liability_share", period)
    # Where families claim on their shares, no deduction from an applicant
    # who, or whose partner, is blind or gets a qualifying disability benefit,
    # whatever the other claimants get (the councils' schemes follow
    # SI 2012/2886 Sch para 30(6)). A single claim's exemption is applied to
    # each non-dependant's deduction.
    applicant_exempt = benunit.household(
        "council_tax_reduction_claims_are_joint", period
    ) & benunit("council_tax_reduction_applicant_has_non_dep_exemption", period)
    return where(
        applicant_exempt, 0, (deductions_in_household - deduction_for_benunit) * share
    )


def normal_gross_income_non_dep_deduction(
    person,
    period,
    ctr,
    working_age,
    exempt_income_based_benefits=True,
    exempt_uc_no_earned_income=True,
):
    gross_income_components = [
        "employment_income",
        "self_employment_income",
        "property_income",
        "private_pension_income",
        "savings_interest_income",
        "dividend_income",
        "state_pension",
    ]
    earned_income_components = [
        "employment_income",
        "self_employment_income",
    ]
    gross_income = add(person, period, gross_income_components)
    earned_income = add(person, period, earned_income_components)
    weekly_benunit_gross_income = person.benunit.sum(gross_income) / WEEKS_IN_YEAR
    weekly_benunit_earned_income = person.benunit.sum(earned_income) / WEEKS_IN_YEAR
    benunit_weekly_hours = person.benunit.max(person("weekly_hours", period))
    in_remunerative_work = (
        benunit_weekly_hours >= ctr.non_dep_deduction.remunerative_work_hours
    )
    weekly_deduction = where(
        in_remunerative_work,
        ctr.non_dep_deduction.amount.calc(weekly_benunit_gross_income),
        ctr.non_dep_deduction.amount.calc(0),
    )
    # The exemption of a household's single claim. Joint claims are exempted
    # one by one, in local_non_dep_deductions.
    claimant_exempt = person.household(
        "council_tax_reduction_household_has_non_dep_exemption", period
    ) & ~person.household("council_tax_reduction_claims_are_joint", period)
    full_time_student = is_full_time_student_non_dep(person, period)
    income_based_benefit = (
        (person.benunit("income_support", period) > 0)
        | (person.benunit("jsa_income", period) > 0)
        | (person.benunit("esa_income", period) > 0)
        | (person.benunit("pension_credit", period) > 0)
    )
    has_uc = person.benunit("universal_credit", period) > 0
    no_earned_income = weekly_benunit_earned_income <= 0
    exempt = (
        claimant_exempt
        | full_time_student
        | (exempt_income_based_benefits & income_based_benefit)
        | (exempt_uc_no_earned_income & has_uc & no_earned_income)
    )
    return working_age * where(exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR)

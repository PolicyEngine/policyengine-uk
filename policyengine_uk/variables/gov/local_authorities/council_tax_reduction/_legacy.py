from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)


def is_full_time_student_non_dep(person, period):
    return (person("current_education", period) != EducationType.NOT_IN_EDUCATION) | (
        person("in_HE", period)
    )


def legacy_council_tax_reduction(
    benunit,
    period,
    ctr,
    working_age,
    non_dep_deductions_variable,
    maximum_support_rate=None,
    maximum_eligible_liability_variable=None,
    applicable_amount=None,
    applicable_income=None,
    additional_applicable_income=0,
):
    is_household_head_benunit = benunit("benunit_contains_household_head", period)
    would_claim = benunit("would_claim_council_tax_reduction", period)
    applicable_amount = (
        benunit("council_tax_reduction_applicable_amount", period)
        if applicable_amount is None
        else applicable_amount
    )
    applicable_income = (
        benunit("council_tax_reduction_applicable_income", period)
        if applicable_income is None
        else applicable_income
    )
    applicable_income += additional_applicable_income
    relevant_income_based_benefit = benunit(
        "council_tax_reduction_relevant_income_based_benefit",
        period,
    )
    liability = (
        benunit.household(maximum_eligible_liability_variable, period)
        if maximum_eligible_liability_variable
        else benunit.household("council_tax", period)
    )
    non_dep_deductions = benunit(non_dep_deductions_variable, period)
    max_support = (
        maximum_support_rate
        if maximum_support_rate is not None
        else ctr.maximum_support_rate
    )
    excess_income = max_(0, applicable_income - applicable_amount)
    excess_income = where(working_age & relevant_income_based_benefit, 0, excess_income)
    preliminary_award = max_(
        0,
        liability * max_support
        - excess_income * ctr.means_test.withdrawal_rate
        - non_dep_deductions,
    )
    capital_eligible = (
        benunit.household("savings", period) <= ctr.means_test.capital_limit
    )
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
    return deductions_in_household - deduction_for_benunit


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
    gross_income = add(person, period, gross_income_components)
    earned_income = person("employment_income", period) + person(
        "self_employment_income", period
    )
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
    claimant_exempt = person.household(
        "council_tax_reduction_household_has_non_dep_exemption", period
    )
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


def earned_income_non_dep_deduction(
    person,
    period,
    ctr,
    working_age,
    exempt_income_based_benefits=True,
    exempt_uc_no_earned_income=False,
    exempt_under_25_uc_no_earned_income=False,
):
    earned_income = person("employment_income", period) + person(
        "self_employment_income", period
    )
    weekly_earned_income = person.benunit.sum(earned_income) / WEEKS_IN_YEAR
    deduction = ctr.non_dep_deduction.amount.calc(weekly_earned_income) * WEEKS_IN_YEAR
    claimant_exempt = person.household(
        "council_tax_reduction_household_has_non_dep_exemption", period
    )
    full_time_student = is_full_time_student_non_dep(person, period)
    income_based_benefit = (
        (person.benunit("income_support", period) > 0)
        | (person.benunit("jsa_income", period) > 0)
        | (person.benunit("esa_income", period) > 0)
        | (person.benunit("pension_credit", period) > 0)
    )
    has_uc = person.benunit("universal_credit", period) > 0
    no_earned_income = weekly_earned_income <= 0
    uc_exempt = (
        has_uc
        & no_earned_income
        & (
            exempt_uc_no_earned_income
            | (exempt_under_25_uc_no_earned_income & (person("age", period) < 25))
        )
    )
    exempt = (
        claimant_exempt
        | full_time_student
        | (exempt_income_based_benefits & income_based_benefit)
        | uc_exempt
    )
    return working_age * where(exempt, 0.0, deduction)


def flat_non_dep_deduction(person, period, ctr, working_age):
    deduction = ctr.non_dep_deduction.amount * WEEKS_IN_YEAR
    claimant_exempt = person.household(
        "council_tax_reduction_household_has_non_dep_exemption", period
    )
    full_time_student = is_full_time_student_non_dep(person, period)
    return working_age * where(claimant_exempt | full_time_student, 0.0, deduction)

from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)


def in_other_non_liable_family(person, period):
    """Whether each person is in a family that neither claims Council Tax
    Reduction for the household nor is liable for the rent: outside every
    applicant's family, and not jointly liable or paying an applicant (SI
    2012/2885 reg 9(2)(a), (d)-(e)). The eligibility for a non-dependant
    deduction uses this, for the national and local schemes alike."""
    return ~person.benunit(
        "council_tax_reduction_claimant_benunit", period
    ) & ~person.benunit("benunit_is_rent_liable", period)


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
    uc_applicable_income = (
        benunit("uc_earned_income", period)
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
    # Every eligible person in the household is a non-dependant of each
    # claiming family: the claimant's own family has only its benefit-unit
    # non-dependants, and jointly liable sharers are not non-dependants (each
    # scheme's para 9, the Default Scheme's wording).
    person = benunit.members
    deductions = person(individual_deduction_variable, period)
    # Only one deduction for a couple, the higher (para 30(3) of each scheme;
    # Oxford para 44), except that Merton's and Kingston upon Thames's
    # schemes deduct for each member of a couple with a Universal Credit
    # award. Any other adult in the family is a non-dependant in their own
    # right.
    claimant_or_partner = person("is_claimant_or_partner", period)
    higher_of_couple = (
        person.get_rank(person.benunit, -deductions, condition=claimant_or_partner) == 0
    )
    each_member_deducted = False
    if not one_deduction_for_uc_couples:
        each_member_deducted = person.benunit("universal_credit", period) > 0
    counted_member = where(
        claimant_or_partner, higher_of_couple | each_member_deducted, True
    )
    counted = deductions * counted_member
    # Members of the applicant's own family are not its non-dependants (para
    # 9(2)(a)), as in council_tax_reduction_non_dep_deductions.
    own_family_member = ~person(
        "is_benefit_unit_non_dependant_for_legacy_benefits", period
    )
    non_dependants = benunit.max(person.household.sum(counted)) - benunit.sum(
        counted * own_family_member
    )
    # A non-dependant of two or more jointly liable people is apportioned
    # equally between them (SI 2012/2885 Sch 1 para 8(5)).
    share = benunit("council_tax_reduction_joint_liability_share", period)
    claims = benunit("council_tax_reduction_claimant_benunit", period)
    # No deduction from an applicant who, or whose partner, is blind or gets a
    # qualifying disability benefit, whatever other claimants in the household
    # get (the councils' schemes follow SI 2012/2886 Sch para 30(6)).
    applicant_exempt = benunit(
        "council_tax_reduction_applicant_has_non_dep_exemption", period
    )
    return where(applicant_exempt, 0, claims * share * non_dependants)


def normal_gross_income_non_dep_deduction(
    person,
    period,
    ctr,
    in_scheme_area,
    exempt_income_based_benefits=True,
    exempt_uc_no_earned_income=True,
):
    """The deduction a non-dependant brings under one council's scheme.

    It depends on the non-dependant alone. Whether a claimant's award uses it
    (the claimant's own scheme) and whether the claimant is exempt from
    non-dependant deductions are decided per claimant family.
    """
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
    # A couple's joint income (para 30(4) of each scheme; Oxford para 44);
    # another adult in the family is a non-dependant in their own right, on
    # their own income.
    claimant_or_partner = person("is_claimant_or_partner", period)
    couple_gross_income = person.benunit.sum(gross_income * claimant_or_partner)
    weekly_gross_income = (
        where(claimant_or_partner, couple_gross_income, gross_income) / WEEKS_IN_YEAR
    )
    # Remunerative work is each person's own (para 10 and para 30(1)(a)). A
    # couple paying one deduction pays the higher, so the working member's
    # band on their joint income.
    in_remunerative_work = (
        person("weekly_hours", period) >= ctr.non_dep_deduction.remunerative_work_hours
    )
    weekly_deduction = where(
        in_remunerative_work,
        ctr.non_dep_deduction.amount.calc(weekly_gross_income),
        ctr.non_dep_deduction.amount.calc(0),
    )
    full_time_student = is_full_time_student_non_dep(person, period)
    # Benefit-unit awards are the claimant's and partner's: another adult in
    # the unit is not on them.
    income_based_benefit = claimant_or_partner & (
        (person.benunit("income_support", period) > 0)
        | (person.benunit("jsa_income", period) > 0)
        | (person.benunit("esa_income", period) > 0)
        | (person.benunit("pension_credit", period) > 0)
    )
    has_uc = claimant_or_partner & (person.benunit("universal_credit", period) > 0)
    # The award is the couple's, so it is calculated on their joint earned
    # income.
    no_earned_income = person.benunit.sum(earned_income * claimant_or_partner) <= 0
    exempt = (
        full_time_student
        | (exempt_income_based_benefits & income_based_benefit)
        | (exempt_uc_no_earned_income & has_uc & no_earned_income)
    )
    return in_scheme_area * where(exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR)

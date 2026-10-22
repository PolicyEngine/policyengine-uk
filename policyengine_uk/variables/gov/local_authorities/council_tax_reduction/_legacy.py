from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
    deduction_per_family,
    has_earned_income,
)
from policyengine_uk.variables.household.demographic.highest_education import (
    EducationType,
)


def in_other_non_liable_family(person, period):
    """Whether each person is outside every family claiming Council Tax
    Reduction for the household, outside every family liable for a share of
    its rent, and not paying the householder for their own occupation: all
    such people aged 18 or over are the applicants' non-dependants (SI
    2012/2885 reg 9(2)(a), (d)-(e) and the Welsh and Scottish equivalents).
    The eligibility for a non-dependant deduction uses this, for the national
    and local schemes alike."""
    return (
        ~person.benunit("council_tax_reduction_claimant_benunit", period)
        & ~person.benunit("liable_for_share_of_household_rent", period)
        & ~person("pays_rent_to_householder", period)
    )


def is_full_time_student_non_dep(person, period):
    return (person("current_education", period) != EducationType.NOT_IN_EDUCATION) | (
        person("in_HE", period)
    )


def applicant_has_universal_credit(benunit, period):
    """Whether the Council Tax Reduction applicant has the benefit unit's
    Universal Credit award. The award belongs to the benefit unit's claimant
    and partner, so not to a household head who applies alone."""
    return (benunit("universal_credit", period) > 0) & ~benunit(
        "council_tax_reduction_head_applies_alone", period
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
    has_uc_award = applicant_has_universal_credit(benunit, period)
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
    """A claiming family's non-dependant deductions under one council's
    scheme, in the shape of council_tax_reduction_non_dep_deductions. Every
    eligible person in the household normally resides with each liable
    applicant, so is a non-dependant of each claiming family (para 9 of each
    scheme, the Default Scheme's wording): another family's adult, or an adult
    in the claiming family's own benefit unit who is not its applicant,
    partner or a child or young person."""
    person = benunit.members
    deductions = person(individual_deduction_variable, period)
    # Only one deduction for a couple, the higher (para 30(3) of each scheme;
    # Oxford para 44), except where the couple has an award of Universal
    # Credit in the schemes that keep the Default Scheme's exception. Any
    # other adult in a family is a non-dependant in their own right.
    each_member_of_uc_couple = False
    if not one_deduction_for_uc_couples:
        each_member_of_uc_couple = benunit("universal_credit", period) > 0
    family_amount = deduction_per_family(
        benunit, period, deductions, each_member_of_uc_couple
    )
    # Each family's amount counted once.
    counted = person("is_benunit_head", period) * benunit.project(family_amount)
    in_household = benunit.max(person.household.sum(counted))
    # Members of the applicant's own family are not its non-dependants (para
    # 9(2)(a)); the non-dependants in its benefit unit are.
    in_unit = person("is_benefit_unit_non_dependant_for_council_tax_reduction", period)
    own_in_unit = deduction_per_family(
        benunit, period, deductions * in_unit, each_member_of_uc_couple
    )
    non_dependants = in_household - family_amount + own_in_unit
    # A non-dependant of two or more jointly liable people is apportioned
    # equally between them (para 30(5) of each scheme).
    share = benunit("council_tax_reduction_joint_liability_share", period)
    # Only a family that claims bears deductions; a non-dependant's own family
    # does not.
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
        "property_income_after_finance_costs",
        "private_pension_income",
        "savings_interest_income",
        "dividend_income",
        "state_pension",
    ]
    gross_income = add(person, period, gross_income_components)
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
    # No deduction for a non-dependant "who is on" Income Support, State
    # Pension Credit, income-based JSA or income-related ESA (para 30(8)(a)):
    # an award payable to them (Default Scheme Sch para 2(3)-(4)). Of a couple,
    # only the payee is on the couple's award, and another member of their
    # benefit unit is on it only through an award of their own.
    income_based_benefit = (
        person("is_on_income_support", period)
        | person("is_on_income_based_jsa", period)
        | person("is_on_income_related_esa", period)
        | person("is_on_pension_credit", period)
    )
    # Nor for one entitled to Universal Credit "calculated on the basis that
    # the person does not have any earned income" (para 30(8)(c)): both joint
    # claimants are entitled to a couple's award, and each is tested on their
    # own earned income, as in the national schemes
    # (council_tax_reduction_non_dep_deduction_exempt).
    universal_credit_without_earned_income = person(
        "is_on_universal_credit", period
    ) & ~has_earned_income(person, period)
    exempt = (
        full_time_student
        | (exempt_income_based_benefits & income_based_benefit)
        | (exempt_uc_no_earned_income & universal_credit_without_earned_income)
    )
    return in_scheme_area * where(exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR)

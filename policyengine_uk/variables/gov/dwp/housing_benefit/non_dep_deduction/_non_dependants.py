"""Shared definitions for Housing Benefit and Council Tax Reduction
non-dependant deductions."""

from policyengine_uk.model_api import *

# Family benefits counted in a couple's gross income, besides Universal Credit.
# None is taxable, so total_income leaves them out.
FAMILY_GROSS_INCOME_BENEFITS = [
    "child_tax_credit",
    "working_tax_credit",
    "child_benefit",
    "income_support",
    "jsa_income",
    "esa_income",
    "pension_credit",
]

# A person's gross income outside total_income: statutory payments, which are
# earnings (HB Regs 2006 reg 35(1)(i); UC Regs 2013 reg 55(4)) the model
# keeps apart from employment income, and Maternity Allowance, which is
# untaxed.
PERSONAL_GROSS_INCOME_OUTSIDE_TOTAL_INCOME = [
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
    "maternity_allowance",
]

# Statutory payments treated as employed earnings (UC Regs 2013 reg 55(4)).
# Statutory adoption, shared parental, parental bereavement and neonatal care
# pay have no input.
STATUTORY_PAY_EARNINGS = [
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
]

# Benefits the benefit cap counts, other than Housing Benefit (benefit_cap_reduction).
CAPPED_BENEFITS_EXCEPT_HOUSING_BENEFIT = [
    "child_benefit",
    "child_tax_credit",
    "jsa_income",
    "income_support",
    "esa_income",
    "universal_credit_pre_benefit_cap",
    "jsa_contrib",
    "incapacity_benefit",
    "esa_contrib",
    "sda",
]


def non_dependant_weekly_gross_income(person, period):
    """Normal weekly gross income for the deduction bands. A claimant or
    partner is banded on the couple's joint income (HB reg 74(4); CTR Sch 1
    para 8(4)): each member's own income plus the family's Universal Credit,
    tax credits, child benefit, Income Support, income-based JSA,
    income-related ESA and Pension Credit. Anyone else in the benefit unit is a
    separate non-dependant, banded on their own income. A person's own income
    is their taxable income plus statutory sick, maternity and paternity pay
    and Maternity Allowance. It leaves out the disability benefits HB reg
    74(9) disregards, which are untaxed."""
    claimant_or_partner = person("is_claimant_or_partner", period)
    own_income = max_(0, person("total_income", period)) + add(
        person, period, PERSONAL_GROSS_INCOME_OUTSIDE_TOTAL_INCOME
    )
    family_benefits = universal_credit_after_benefit_cap(person.benunit, period) + sum(
        person.benunit(benefit, period) for benefit in FAMILY_GROSS_INCOME_BENEFITS
    )
    couple_income = (
        person.benunit.sum(own_income * claimant_or_partner) + family_benefits
    )
    annual = where(claimant_or_partner, couple_income, own_income)
    return annual / WEEKS_IN_YEAR


def universal_credit_after_benefit_cap(benunit, period):
    """A family's Universal Credit award after the benefit cap (UC Regs 2013
    reg 81), for a family that is not liable for rent. universal_credit itself
    depends on Housing Benefit through the cap, so the cap is applied here to
    the capped benefits other than Housing Benefit, which such a family does
    not receive. The award is reduced by the excess minus the childcare costs
    element, and not at all where that element is greater than the excess
    (reg 81(1)-(2))."""
    capped = sum(
        benunit(benefit, period) for benefit in CAPPED_BENEFITS_EXCEPT_HOUSING_BENEFIT
    )
    excess = max_(0, capped - benunit("benefit_cap", period))
    reduction = max_(0, excess - benunit("uc_childcare_element", period))
    return max_(0, benunit("universal_credit_pre_benefit_cap", period) - reduction)


def has_earned_income(person, period):
    """Whether the person has earned income (UC Regs 2013 reg 52): employed
    earnings, including statutory sick, maternity and paternity pay and less
    relievable pension contributions (reg 55(4)-(5)); self-employed earnings,
    a loss counting as nil and less any relievable pension contributions not
    already deducted from employed earnings (reg 57(2), steps 3-4), with the
    minimum income floor applying where the Universal Credit model applies it
    (reg 62); and other paid work."""
    pension_contributions = person("pension_contributions", period)
    employed_gross = add(person, period, ["employment_income", *STATUTORY_PAY_EARNINGS])
    has_employed_earnings = employed_gross > 0
    employed = max_(0, employed_gross - pension_contributions)
    # Contributions are deducted from employed earnings where there are any
    # (reg 55(5)(a)), and otherwise from self-employed earnings (reg 57(2),
    # step 4).
    self_employed = max_(
        0,
        max_(0, person("self_employment_income", period))
        - where(has_employed_earnings, 0, pension_contributions),
    )
    self_employed = where(
        person("uc_mif_applies", period),
        max_(self_employed, person("uc_minimum_income_floor", period)),
        self_employed,
    )
    other = max_(0, person("miscellaneous_income", period))
    return (employed + self_employed + other) > 0


def is_award_payee(person, period, award, reported):
    """Whether a family award is payable to this person: Housing Benefit's
    test for being "on" income-based JSA or income-related ESA (HB Regs 2006
    reg 2(3) and (3A)), applied also to Income Support and State Pension
    Credit, which are paid to the claimant. The payee is the member who
    reports the award, or the benefit unit's head where none does. Both
    members of a joint-claim jobseeker's allowance couple are on it (reg
    2(3)(c)), but the model has no joint-claim input, so only the payee is."""
    has_award = person.benunit(award, period) > 0
    reports = person(reported, period) > 0
    payee = where(
        person.benunit.any(reports), reports, person("is_benunit_head", period)
    )
    return has_award & payee


def deduction_per_family(benunit, period, deductions, both_members_of_couple):
    """One deduction for the claimant and partner, the higher of theirs (HB reg
    74(3); CTR Sch 1 para 8(3)), or both where both_members_of_couple; plus a
    separate deduction for each other member."""
    claimant_or_partner = benunit.members("is_claimant_or_partner", period)
    couple = where(
        both_members_of_couple,
        benunit.sum(deductions * claimant_or_partner),
        benunit.max(deductions * claimant_or_partner),
    )
    return couple + benunit.sum(deductions * ~claimant_or_partner)


def charged_to_other_families(benunit, period, deduction_for_benunit):
    """Deductions for the non-dependant families in the household other than
    this one: each family's amount counted once (via its head)."""
    is_benunit_head = benunit.members("is_benunit_head", period)
    counted = is_benunit_head * benunit.project(deduction_for_benunit)
    in_household = benunit.max(benunit.members.household.sum(counted))
    return in_household - deduction_for_benunit

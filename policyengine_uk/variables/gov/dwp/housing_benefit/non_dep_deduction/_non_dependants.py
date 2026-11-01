"""Shared definitions for Housing Benefit and Council Tax Reduction
non-dependant deductions."""

from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_cap import benefit_cap_couple
from policyengine_uk.utils.benefit_unit import add_for_members, award_of_couple
from policyengine_uk.variables.gov.dwp.benefit_cap_welfare_benefits import (
    CLAIMANT_OR_PARTNER_BENEFITS as CAPPED_CLAIMANT_OR_PARTNER_BENEFITS,
    FAMILY_BENEFITS as CAPPED_FAMILY_BENEFITS,
)
from policyengine_uk.variables.gov.dwp.esa_income import (
    income_related_esa_award_on_reports,
)
from policyengine_uk.variables.gov.dwp.jsa_income import (
    income_related_jsa_award_on_reports,
)

# Family benefits counted in a couple's gross income, besides Universal Credit.
# They are awarded to the benefit unit, so the person-level gross income
# variables leave them out.
FAMILY_GROSS_INCOME_BENEFITS = [
    "child_tax_credit",
    "working_tax_credit",
    "child_benefit",
    "income_support",
    "jsa_income",
    "esa_income",
    "pension_credit",
]

# Statutory payments treated as employed earnings (UC Regs 2013 reg 55(4)).
# Statutory adoption, shared parental, parental bereavement and neonatal care
# pay have no input.
STATUTORY_PAY_EARNINGS = [
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
]

# The welfare benefits the benefit cap counts (benefit_cap_welfare_benefits)
# other than Housing Benefit, and Maternity Allowance, a welfare benefit
# (Welfare Reform Act 2012 s.96(10)(i)) that total leaves out. Bereavement
# allowance and the widow's benefits have no input.
CAPPED_BENEFITS_EXCEPT_HOUSING_BENEFIT = [
    benefit
    for benefit in CAPPED_CLAIMANT_OR_PARTNER_BENEFITS + CAPPED_FAMILY_BENEFITS
    if benefit != "housing_benefit_pre_benefit_cap"
] + ["maternity_allowance"]


def non_dependant_weekly_gross_income(person, period, own_gross_income):
    """Normal weekly gross income for the deduction bands. A claimant or
    partner is banded on the couple's joint income (HB reg 74(4); CTR Sch 1
    para 8(4)): each member's own gross income plus the family's Universal
    Credit, tax credits, child benefit, Income Support, income-based JSA,
    income-related ESA and Pension Credit. Anyone else in the benefit unit is
    a separate non-dependant, banded on their own income. own_gross_income
    names the programme's person-level gross income variable."""
    claimant_or_partner = person("is_claimant_or_partner", period)
    own_income = person(own_gross_income, period)
    benunit = person.simulation.populations["benunit"]
    family_benefits = universal_credit_after_benefit_cap(benunit, period) + add(
        benunit, period, FAMILY_GROSS_INCOME_BENEFITS
    )
    couple_income = person.benunit.sum(
        own_income * claimant_or_partner
    ) + benunit.project(family_benefits)
    annual = where(claimant_or_partner, couple_income, own_income)
    return annual / WEEKS_IN_YEAR


def universal_credit_after_benefit_cap(benunit, period):
    """A family's Universal Credit award after the benefit cap (UC Regs 2013
    reg 81), for a family that is not liable for rent. universal_credit and
    uc_benefit_cap_reduction depend on Housing Benefit through the welfare
    benefits they count, so the cap (uc_benefit_cap) is applied here to the
    same welfare benefits other than Housing Benefit, which such a family does
    not receive (UC reg 80(2A) counts it as nil in any case), for the same
    single person or couple (benefit_cap_couple; reg 79(1)). The award is
    reduced by the excess minus the childcare costs element, and not at all
    where that element is greater than the excess (reg 81(1)-(2)). Deductions
    paid from the award to third parties or for debts are still the family's
    income, so they are not taken off."""
    couple = benefit_cap_couple(benunit, period)
    income_based = award_of_couple(
        benunit,
        period,
        "jsa_income",
        "jsa_income_reported",
        income_related_jsa_award_on_reports,
        couple,
    ) + award_of_couple(
        benunit,
        period,
        "esa_income",
        "esa_income_reported",
        income_related_esa_award_on_reports,
        couple,
    )
    capped = income_based + add_for_members(
        benunit, period, CAPPED_BENEFITS_EXCEPT_HOUSING_BENEFIT, couple
    )
    excess = max_(0, capped - benunit("uc_benefit_cap", period))
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


def is_on_legacy_income_related_benefit(person, period):
    """Whether the person is on Income Support, income-based JSA or
    income-related ESA: the award is payable to them (HB Regs 2006 reg 2(1),
    (3) and (3A); the Council Tax Reduction schemes use the same
    definitions)."""
    return (
        person("is_on_income_support", period)
        | person("is_on_income_based_jsa", period)
        | person("is_on_income_related_esa", period)
    )


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

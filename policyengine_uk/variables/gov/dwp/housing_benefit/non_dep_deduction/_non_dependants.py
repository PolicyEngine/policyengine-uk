"""Shared definitions for Housing Benefit and Council Tax Reduction
non-dependant deductions."""

from policyengine_uk.model_api import *

# Family benefits counted in a couple's gross income. Universal Credit is taken
# before the benefit cap: the capped award depends on Housing Benefit.
FAMILY_GROSS_INCOME_BENEFITS = [
    "universal_credit_pre_benefit_cap",
    "child_tax_credit",
    "working_tax_credit",
    "child_benefit",
]


def non_dependant_weekly_gross_income(person, period):
    """Normal weekly gross income for the deduction bands. A claimant or
    partner is banded on the couple's joint income (HB reg 74(4); CTR Sch 1
    para 8(4)): each member's taxable income plus the family's Universal
    Credit, tax credits and child benefit. Anyone else in the benefit unit is a
    separate non-dependant, banded on their own taxable income. Taxable income
    excludes the disregarded disability benefits (HB reg 74(9))."""
    claimant_or_partner = person("is_claimant_or_partner", period)
    own_income = max_(0, person("total_income", period))
    family_benefits = sum(
        person.benunit(benefit, period) for benefit in FAMILY_GROSS_INCOME_BENEFITS
    )
    couple_income = (
        person.benunit.sum(own_income * claimant_or_partner) + family_benefits
    )
    annual = where(claimant_or_partner, couple_income, own_income)
    return annual / WEEKS_IN_YEAR


def has_earned_income(person, period):
    """Whether the person has earned income (UC Regs 2013 reg 52), with
    self-employed losses taken as nil (reg 57(2), step 3)."""
    return (
        max_(0, person("employment_income", period))
        + max_(0, person("self_employment_income", period))
    ) > 0


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

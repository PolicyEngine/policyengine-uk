"""Shared definitions for Housing Benefit and Council Tax Reduction
non-dependant deductions."""

from policyengine_uk.model_api import *

# Family benefits counted in a couple's gross income, besides Universal Credit.
FAMILY_GROSS_INCOME_BENEFITS = [
    "child_tax_credit",
    "working_tax_credit",
    "child_benefit",
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


def is_claimant_or_partner(person, period):
    """The claimant or partner of a benefit unit: its head, or any member who
    is not a child or qualifying young person (SSCBA 1992 s.142), which is how
    the Housing Benefit Regulations 2006 (regs 2(1) and 19) and the English and
    Welsh Council Tax Reduction regulations (reg 2(1)) define the members of a
    family other than the claimant and partner."""
    return person("is_benunit_head", period) | ~person(
        "is_child_or_qualifying_young_person_for_child_benefit", period
    )


def non_dependant_weekly_gross_income(person, period):
    """Normal weekly gross income for the deduction bands. A claimant or
    partner is banded on the couple's joint income (HB reg 74(4); CTR Sch 1
    para 8(4)): each member's taxable income plus the family's Universal
    Credit, tax credits and child benefit. Anyone else in the benefit unit is a
    separate non-dependant, banded on their own taxable income. Taxable income
    excludes the disregarded disability benefits (HB reg 74(9))."""
    claimant_or_partner = is_claimant_or_partner(person, period)
    own_income = max_(0, person("total_income", period))
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
    not receive."""
    capped = sum(
        benunit(benefit, period) for benefit in CAPPED_BENEFITS_EXCEPT_HOUSING_BENEFIT
    )
    reduction = max_(0, capped - benunit("benefit_cap", period))
    return max_(0, benunit("universal_credit_pre_benefit_cap", period) - reduction)


def has_earned_income(person, period):
    """Whether the person has earned income (UC Regs 2013 reg 52): employed
    earnings, including statutory sick and maternity pay and less relievable
    pension contributions (reg 55(4)-(5)); self-employed earnings, a loss
    counting as nil (reg 57(2)) and the minimum income floor applying where
    the Universal Credit model applies it (reg 62); and other paid work."""
    employed = max_(
        0,
        add(
            person,
            period,
            ["employment_income", "statutory_sick_pay", "statutory_maternity_pay"],
        )
        - person("pension_contributions", period),
    )
    self_employed = max_(0, person("self_employment_income", period))
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
    reports the award, or the benefit unit's head where none does."""
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
    claimant_or_partner = is_claimant_or_partner(benunit.members, period)
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

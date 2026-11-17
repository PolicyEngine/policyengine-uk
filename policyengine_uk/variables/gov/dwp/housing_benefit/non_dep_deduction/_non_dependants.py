"""Shared definitions for Housing Benefit and Council Tax Reduction
non-dependant deductions."""

from policyengine_uk.model_api import *

# Family benefits counted in a couple's gross income, besides Universal Credit.
# They are awarded to the benefit unit, so the person-level gross income
# variables leave them out. Income-based JSA and income-related ESA count the
# claimant's and partner's award only: another member claims in their own
# right.
FAMILY_GROSS_INCOME_BENEFITS = [
    "child_tax_credit",
    "working_tax_credit",
    "child_benefit",
    "income_support",
    "claimant_or_partner_jsa_income",
    "claimant_or_partner_esa_income",
    "pension_credit",
]


def non_dependant_weekly_gross_income(person, period, parameters, own_gross_income):
    """Calculate normal weekly gross income for the deduction bands. The council
    bands a claimant or partner on the couple's joint income (HB reg 74(4); CTR
    Sch 1 para 8(4)): each member's own gross income plus the family's tax credits,
    child benefit, Income Support, income-based JSA, income-related ESA and
    Pension Credit, and its Universal Credit award (universal_credit_award)
    where either member claims it. The council bands each other member of the
    benefit unit separately on their own income, adding Universal Credit
    where that member claims it alone. own_gross_income names the programme's
    person-level gross income variable.
    """
    claimant_or_partner = person("is_claimant_or_partner", period)
    own_income = person(own_gross_income, period)
    benunit = person.simulation.populations["benunit"]
    other_awards = benunit.project(add(benunit, period, FAMILY_GROSS_INCOME_BENEFITS))
    # Universal Credit is the income of the claimants it assesses, the
    # claimant and partner unless is_uc_claimant names someone else.
    universal_credit = benunit.project(universal_credit_award(benunit, period))
    uc_claimant = person("is_uc_assessed_claimant", period)
    couple_claims_universal_credit = person.benunit.any(
        uc_claimant & claimant_or_partner
    )
    couple_income = (
        person.benunit.sum(own_income * claimant_or_partner)
        + other_awards
        + where(couple_claims_universal_credit, universal_credit, 0)
    )
    single_income = own_income + where(
        uc_claimant & ~couple_claims_universal_credit, universal_credit, 0
    )
    annual = where(claimant_or_partner, couple_income, single_income)
    return annual / WEEKS_IN_YEAR


def universal_credit_award(benunit, period):
    """Return a family's Universal Credit award after the benefit cap (UC
    Regs 2013 reg 81) and before debt deductions. Welfare Reform Act 2012
    s.8(1) sets the award as the maximum amount less the amounts for
    income. DWP then takes advances (SI 2013/383 reg 10), overpayments (SI
    2013/384 regs 10-11) and third-party payments (SI 2013/380 Sch 6 para
    2(1)) from the sum payable, so those deductions stay the family's
    income. A nil award carries none."""
    universal_credit = benunit("universal_credit", period)
    deductions = benunit("uc_deductions", period)
    return universal_credit + where(universal_credit > 0, deductions, 0)


def has_earned_income(person, period):
    """Read whether Universal Credit counts positive earned income for the
    person (uc_individual_earned_income). HB Regs 2006 reg 74(8)(b), (11) and
    the CTR schemes' equivalents give "earned income" the meaning in UC Regs
    2013 reg 52. UC deducts allowable expenses, tax, National Insurance and
    relievable pension contributions (reg 55(3), (5)); attributes company
    income to its owner (reg 77(3)); offsets trading losses (reg 57(2)); and
    applies the floor under reg 62, a couple's floor included."""
    return person("uc_individual_earned_income", period) > 0


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

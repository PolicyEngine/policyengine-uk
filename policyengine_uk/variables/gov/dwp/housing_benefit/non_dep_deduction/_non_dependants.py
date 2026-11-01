"""Shared definitions for Housing Benefit and Council Tax Reduction
non-dependant deductions."""

from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_cap import benefit_cap_couple
from policyengine_uk.utils.benefit_unit import add_for_members, award_of_couple
from policyengine_uk.utils.supplied_inputs import stored_as_input
from policyengine_uk.variables.gov.dwp.benefit_cap_welfare_benefits import (
    CLAIMANT_OR_PARTNER_BENEFITS as CAPPED_CLAIMANT_OR_PARTNER_BENEFITS,
    FAMILY_BENEFITS as CAPPED_FAMILY_BENEFITS,
)
from policyengine_uk.variables.gov.dwp.universal_credit.benefit_cap.uc_benefit_cap_reduction import (
    benefit_cap_reduction_of,
)
from policyengine_uk.variables.gov.dwp.universal_credit.benefit_cap.uc_benefit_cap_reduction_after_floor import (
    benefit_cap_reduction_applied,
)
from policyengine_uk.variables.gov.dwp.universal_credit.universal_credit import (
    universal_credit as universal_credit_variable,
)
from policyengine_uk.variables.gov.dwp.esa_income import (
    income_related_esa_award_on_reports,
)
from policyengine_uk.variables.gov.dwp.jsa_income import (
    income_related_jsa_award_on_reports,
)

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

# The welfare benefits the benefit cap counts (benefit_cap_welfare_benefits)
# other than Housing Benefit, and Maternity Allowance, a welfare benefit
# (Welfare Reform Act 2012 s.96(10)(i)) that total leaves out. Bereavement
# allowance and the widow's benefits have no input.
CAPPED_BENEFITS_EXCEPT_HOUSING_BENEFIT = [
    benefit
    for benefit in CAPPED_CLAIMANT_OR_PARTNER_BENEFITS + CAPPED_FAMILY_BENEFITS
    if benefit != "housing_benefit_pre_benefit_cap"
] + ["maternity_allowance"]


def non_dependant_weekly_gross_income(person, period, parameters, own_gross_income):
    """Normal weekly gross income for the deduction bands. A claimant or
    partner is banded on the couple's joint income (HB reg 74(4); CTR Sch 1
    para 8(4)): each member's own gross income plus the family's tax credits,
    child benefit, Income Support, income-based JSA, income-related ESA and
    Pension Credit, and its Universal Credit where either member claims it.
    Anyone else in the benefit unit is a separate non-dependant, banded on
    their own income, with the Universal Credit where they alone claim it.
    own_gross_income names the programme's person-level gross income
    variable."""
    claimant_or_partner = person("is_claimant_or_partner", period)
    own_income = person(own_gross_income, period)
    benunit = person.simulation.populations["benunit"]
    other_awards = benunit.project(add(benunit, period, FAMILY_GROSS_INCOME_BENEFITS))
    # Universal Credit is the income of the claimants it assesses, the
    # claimant and partner unless is_uc_claimant names someone else.
    universal_credit = benunit.project(
        universal_credit_after_benefit_cap(benunit, period, parameters)
    )
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


def reads_simulation_value(benunit, period, variable_name, default_formula=None):
    """Whether to read the variable rather than recalculate it here: a value
    stored as an input for the period, a neutralized variable, or, where
    default_formula is given, a formula a reform has replaced."""
    variable = benunit.simulation.tax_benefit_system.get_variable(variable_name)
    if variable.is_neutralized:
        return True
    if default_formula is not None:
        formula = variable.get_formula(period)
        if formula is None or formula.__code__ != default_formula.__code__:
            return True
    return stored_as_input(benunit, variable_name, period)


def universal_credit_after_benefit_cap(benunit, period, parameters):
    """A family's Universal Credit award after the benefit cap (UC Regs 2013
    reg 81), for a family that is not liable for rent. universal_credit and
    uc_benefit_cap_reduction depend on Housing Benefit through the welfare
    benefits they count, so this applies the cap to the same welfare benefits
    other than Housing Benefit, which such a family does not receive (UC reg
    80(2A) counts it as nil in any case), for the same single person or couple
    (benefit_cap_couple; reg 79(1)). It shares the award's own calculation of
    the reduction (benefit_cap_reduction_of) and of the part a protected
    minimum floor lets it take (benefit_cap_reduction_applied). Deductions
    paid from the award to third parties or for debts are still the family's
    income, so they are not taken off, and the floor is applied as for a
    family with none: the deduction rate depends on the cap reduction, and so
    on Housing Benefit. A universal_credit stored as an input or given a new
    formula by a reform is read as it is, and so is a stored or neutralized
    uc_benefit_cap_reduction_after_floor, uc_benefit_cap_reduction or
    benefit_cap_welfare_benefits, the last with Housing Benefit at nil."""
    if reads_simulation_value(
        benunit, period, "universal_credit", universal_credit_variable.formula
    ):
        return benunit("universal_credit", period)
    if reads_simulation_value(benunit, period, "uc_benefit_cap_reduction_after_floor"):
        applied = benunit("uc_benefit_cap_reduction_after_floor", period)
    else:
        if reads_simulation_value(benunit, period, "uc_benefit_cap_reduction"):
            reduction = benunit("uc_benefit_cap_reduction", period)
        else:
            reduction = benefit_cap_reduction_of(
                benunit, period, capped_welfare_benefits(benunit, period)
            )
        applied = benefit_cap_reduction_applied(
            benunit, period, parameters, reduction, 0
        )
    return max_(benunit("universal_credit_pre_benefit_cap", period) - applied, 0)


def capped_welfare_benefits(benunit, period):
    """The welfare benefits the Universal Credit cap counts, with Housing
    Benefit at nil (reg 80(2A)) and Maternity Allowance in."""
    if reads_simulation_value(benunit, period, "benefit_cap_welfare_benefits"):
        return benunit("benefit_cap_welfare_benefits", period)
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
    return income_based + add_for_members(
        benunit, period, CAPPED_BENEFITS_EXCEPT_HOUSING_BENEFIT, couple
    )


def has_earned_income(person, period):
    """Whether the person has earned income as Universal Credit calculates it
    (HB Regs 2006 reg 74(8)(b), (11) and the CTR schemes' equivalents give
    "earned income" the meaning in UC Regs 2013 reg 52):
    uc_individual_earned_income, which takes off allowable expenses, tax,
    National Insurance and relievable pension contributions (reg 55(3), (5)),
    counts a company's income attributed to its owner and sets trading losses
    against profits (regs 57(2), 77(3)), and applies the minimum income floor
    only where reg 62 does, a couple's floor included."""
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

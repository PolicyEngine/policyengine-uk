from policyengine_uk.model_api import *
from policyengine_uk.utils.supplied_inputs import replaces_formula, stored_as_input
from policyengine_uk.variables.gov.dwp.pension_credit.guarantee_credit.guarantee_credit import (
    guarantee_credit,
)
from policyengine_uk.variables.gov.dwp.pension_credit.is_pension_credit_eligible import (
    is_pension_credit_eligible,
)
from policyengine_uk.variables.gov.dwp.pension_credit.pension_credit import (
    pension_credit,
)
from policyengine_uk.variables.gov.dwp.pension_credit.pension_credit_entitlement import (
    pension_credit_entitlement,
)
from policyengine_uk.variables.gov.dwp.pension_credit.savings_credit.savings_credit import (
    savings_credit,
)

# The branch in which the family has no income-related ESA.
NO_INCOME_RELATED_ESA_BRANCH = "esa_income_pension_credit_bar"

# The Pension Credit variables whose formulas the model's age and take-up
# conditions govern, with pension_credit_entitlement, which sums two of them.
PENSION_CREDIT_FORMULAS = [
    pension_credit,
    is_pension_credit_eligible,
    guarantee_credit,
    savings_credit,
]


def pension_credit_follows_model_formulas(benunit, period, parameters):
    """Whether the simulation calculates Pension Credit with the model's own
    formulas, which pay it only to a family that meets the Pension Credit age
    conditions (meets_pension_credit_age_conditions) and would claim
    (would_claim_pc).

    pension_credit equals the entitlement where the family would claim and
    nil otherwise. The entitlement sums the guarantee and savings credits for
    a family eligible for Pension Credit (is_pension_credit_eligible), and
    nil for any other, and only a family that meets the age conditions is
    eligible. A parameter reform keeps these formulas, and the age conditions
    read its parameters.

    A caller can instead set pension_credit, its entitlement, its eligibility
    or either credit as an input for the period. A reform can replace or
    remove one of their formulas, change what the entitlement sums or which
    families it covers, or freeze Pension Credit at the baseline's award
    (gov.contrib.freeze_pension_credit) whatever the reform's age conditions.
    Pension Credit can then pay a family that does not meet the age
    conditions or would not claim.
    """
    simulation = benunit.simulation
    if (
        parameters(period).gov.contrib.freeze_pension_credit
        and simulation.baseline is not None
    ):
        return False
    for default in PENSION_CREDIT_FORMULAS:
        if replaces_formula(benunit, default.__name__, period, default.formula):
            return False
    name = pension_credit_entitlement.__name__
    entitlement = simulation.tax_benefit_system.get_variable(name)
    return (
        not entitlement.is_neutralized
        and entitlement.get_formula(period) is None
        and entitlement.adds == pension_credit_entitlement.adds
        and entitlement.defined_for == pension_credit_entitlement.defined_for
        and not stored_as_input(benunit, name, period)
    )


def pension_credit_without_income_related_esa(benunit, period):
    """The Pension Credit the family would get with no income-related ESA.

    Parliament bars the couple's income-related ESA while the claimant, or
    the other member of the couple, has an entitlement to State Pension
    Credit (Welfare Reform Act 2007 Sch 1 para 6(1)(c) and (d)), and the
    model's Pension Credit reads that award. Its higher earnings disregard
    counts the couple's award (claimant_or_partner_esa_income; SPC Regs 2002
    Sch VI para 4(1)(a)(vii)). It counts working tax credit as income, and
    the tax credit income test reads the award (TCA 2002 s.7(2)), as does
    Income Support's gate, which that test reads. Its route test
    (left_pension_route_at_legacy_closure) reads Universal Credit
    entitlement, whose work capability test reads esa_income
    (has_own_esa_award). A formula that read Pension Credit in the
    simulation itself would close a cycle.

    This function calculates Pension Credit in a branch that sets
    esa_income, the couple's award and esa_income_eligible to nil, so the
    screen never runs there. The branch reads pension_credit, so it counts
    the claim (would_claim_pc) and an entered award. Where that Pension
    Credit pays, the screen refuses the couple's award, and the
    simulation's own Pension Credit then equals the branch's. Where it pays
    nothing, the model pays the award. If the award then makes Pension
    Credit pay, through the higher earnings disregard, no consistent state
    exists: with Pension Credit in payment the family could not have the
    award, and without the award it would get no Pension Credit. The model
    then pays the award beside the Pension Credit it works out on it.

    In a year with tax credits, a calculation in this branch opens the
    passport branch (pension_credit_with_passported_tax_credits), and one in
    the passport branch opens this one. Core reads a branch's inputs from
    the branches it was made from as well, so a branch of either keeps both
    sets of inputs.
    """
    simulation = benunit.simulation
    # get_branch returns an existing branch of that name, or this simulation
    # if it has that name, so take a name in use by neither.
    name = NO_INCOME_RELATED_ESA_BRANCH
    while name in simulation.branches or name == simulation.branch_name:
        name += "_"
    branch = simulation.get_branch(name)
    try:
        for variable in ["esa_income", "claimant_or_partner_esa_income"]:
            branch.set_input(variable, period, benunit.empty_array())
        branch.set_input("esa_income_eligible", period, benunit.filled_array(False))
        # Through the population, so a microsimulation returns an
        # unweighted array.
        return branch.populations[benunit.entity.key]("pension_credit", period)
    finally:
        simulation.branches.pop(name, None)


class esa_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether a reported income-related ESA award passes the age, Pension "
        "Credit, capital and work tests"
    )
    documentation = (
        "Bounded age, Pension Credit, work and capital screen for reported "
        "income-related ESA, not a full entitlement model. When an original claimant "
        "or partner reports an open award, only they are candidate claimants; "
        "otherwise other open reporters are candidates. The claimant must not have "
        "reached pensionable age (Welfare Reform Act 2007 s.1(3)(c)): their own State "
        "Pension age (s.1(6)), which is_SP_age places at 6 October of the year. "
        "Neither the claimant nor the other member of the couple may have an "
        "entitlement to State Pension Credit (Sch 1 para 6(1)(c) and (d)). The "
        "model's Pension Credit reads the couple's award, so the screen reads the "
        "Pension Credit the couple would get with no income-related ESA in the "
        "family (pension_credit_without_income_related_esa), which counts the claim "
        "(would_claim_pc) and an entered award, and refuses the couple's claim where "
        "it exceeds nil. The screen works that out for each couple whose claim "
        "passes the other tests, and only where some couple's claim does. Where the "
        "model's own formulas calculate Pension Credit "
        "(pension_credit_follows_model_formulas), they pay it only to a couple that "
        "meets the Pension Credit age conditions (meets_pension_credit_age_conditions) "
        "and would claim, so the screen works it out only for such a couple. Where "
        "the family gets no Pension Credit without the award but gets it with the "
        "award, through the higher earnings disregard the award brings (SPC Regs 2002 "
        "Sch VI para 4(1)(a)(vii)), no consistent state exists, and the family gets "
        "both. A member who claims in their own right keeps their claim whatever the "
        "couple's Pension Credit. The claimant must not engage in remunerative work "
        "(para 6(1)(e); esa_income_claimant_remunerative_work). The other member of "
        "the couple must not engage in remunerative work (para 6(1)(f)): paid work of "
        "24 hours a week or more (ESA Regs 2008 reg 42(1)), subject to the existing "
        "carer exception (reg 43(2)(c); IS Regs 1987 Sch 1B para 4), which the model "
        "reads as is_carer_for_benefits. Assessable capital must remain within the "
        "existing limit (para 6(1)(b); reg 110). The model applies neither para "
        "6(1)(g) (receiving education) nor the other member's income-based JSA under "
        "para 6(1)(d). The Northern Ireland Assembly set the same conditions in the "
        "Welfare Reform Act (Northern Ireland) 2007 s.1(3)(c) and Sch 1 para 6(1)(c) "
        "and (d), but took pensionable age in s.1(6) from the Pensions (Northern "
        "Ireland) Order 1995 Sch 2 para 1, where Parliament took it from the Pensions "
        "Act 1995 Sch 4 para 1. Under either schedule a person born on a given date "
        "reaches pensionable age on the same day, so the model applies one rule "
        "across the UK. The aggregate esa_income uses this screen for its original "
        "couple's part and pays each outside reporter's claim separately, on their "
        "own existing work/capital screen, pensionable age and tariff. The screen "
        "uses the benefit unit's capital as an explicit proxy for unobserved "
        "outside-claim capital. It drops reports whose own award has closed before it "
        "chooses candidates, and ESA also drops the couple's reports on a UC claim. "
        "The separate aggregation leaves this variable's candidate rules unchanged."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2007/5/section/1",
        "https://www.legislation.gov.uk/ukpga/2007/5/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/ukpga/1995/26/schedule/4",
        "https://www.legislation.gov.uk/ukpga/2002/16/section/4",
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/41",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/42",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/43",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/110",
        "https://www.legislation.gov.uk/nia/2007/2/section/1",
        "https://www.legislation.gov.uk/nia/2007/2/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/nisi/1995/3213/schedule/2",
    )

    def formula(benunit, period, parameters):
        ESA = parameters(period).gov.dwp.ESA.income
        person = benunit.members
        capital = benunit("esa_income_assessable_capital", period)
        reports_award = (person("esa_income_reported", period) > 0) & ~person(
            "esa_income_report_closed", period
        )
        claimant_or_partner = person("is_claimant_or_partner", period)
        # The candidate claimants: the claimant or partner who reports the
        # award, or, if neither does, whoever in the benefit unit does.
        couple_reports = benunit.any(reports_award & claimant_or_partner)
        candidate = reports_award & (
            claimant_or_partner | ~benunit.project(couple_reports)
        )
        # WRA 2007 s.1(3)(c): the claimant "has not reached pensionable age"
        # (s.1(6): the age in Pensions Act 1995 Sch 4 para 1). A man born
        # before 6 December 1953 reaches it at 65.
        pensionable_age = person("is_SP_age", period)
        # Para 6(1)(e) and reg 41: the claimant's own remunerative work.
        claimant_works = person("esa_income_claimant_remunerative_work", period)
        # Para 6(1)(f) and reg 42(1): the other member of the couple works 24
        # hours a week or more; reg 43(2)(c): not if a carer.
        hours = person("esa_income_remunerative_work_hours", period)
        works_as_partner = (
            claimant_or_partner
            & ~person("is_carer_for_benefits", period)
            & (hours >= ESA.remunerative_work.partner_hours)
        )
        other_member_works = claimant_or_partner & (
            (benunit.project(benunit.sum(works_as_partner)) - works_as_partner) > 0
        )
        passes = candidate & ~pensionable_age & ~claimant_works & ~other_member_works
        within_capital = capital <= ESA.capital.limit
        couple_passes = benunit.any(passes & claimant_or_partner) & within_capital
        if not couple_passes.any():
            return benunit.any(passes) & within_capital
        # Sch 1 para 6(1)(c) and (d): Parliament allows the income-related
        # allowance only where neither the claimant nor the other member of
        # the couple has an entitlement to State Pension Credit. The model's
        # Pension Credit reads the couple's award, so this reads the couple's
        # Pension Credit without it, for each couple whose claim passes the
        # other tests. The model's own formulas pay Pension Credit only to a
        # couple that meets the age conditions and would claim, so where they
        # calculate it, this reads it only for a couple that does, and only
        # where some couple does. A member who claims in their own right keeps
        # their claim whatever the couple's Pension Credit.
        on_pension_credit = couple_passes
        if pension_credit_follows_model_formulas(benunit, period, parameters):
            on_pension_credit = (
                couple_passes
                & benunit("meets_pension_credit_age_conditions", period)
                & benunit("would_claim_pc", period)
            )
        if on_pension_credit.any():
            on_pension_credit = on_pension_credit & (
                pension_credit_without_income_related_esa(benunit, period) > 0
            )
        pension_credit_bars = claimant_or_partner & benunit.project(on_pension_credit)
        return benunit.any(passes & ~pension_credit_bars) & within_capital

from policyengine_uk.model_api import *

# The branch in which the family has no income-related ESA.
NO_INCOME_RELATED_ESA_BRANCH = "esa_income_pension_credit_bar"


def pension_credit_without_income_related_esa(benunit, period):
    """The Pension Credit the family would get with no income-related ESA.

    Welfare Reform Act 2007 Sch 1 para 6(1)(c) and (d) bar the couple's
    income-related ESA while the claimant, or the other member of the couple,
    has an entitlement to State Pension Credit, and Pension Credit reads that
    award.
    Its higher earnings disregard counts the couple's award
    (claimant_or_partner_esa_income; SPC Regs 2002 Sch VI para
    4(1)(a)(vii)). Working tax credit counts as Pension Credit income, and
    the tax credit income test reads the award (TCA 2002 s.7(2)), as does
    Income Support's gate, which that test reads. Pension Credit's route test
    (left_pension_route_at_legacy_closure) reads Universal Credit
    entitlement, whose work capability test reads esa_income
    (has_own_esa_award). Reading Pension Credit in the simulation itself
    would close a cycle.

    This calculates Pension Credit in a branch that sets esa_income, the
    couple's award and esa_income_eligible to nil, so the screen never runs
    there. The branch reads pension_credit, so the claim (would_claim_pc)
    and an entered award count. Where it pays, the bar holds: the screen
    refuses the couple's award, and the simulation's own Pension Credit then
    equals the branch's. Where it pays nothing, the award stands. If the
    award then makes Pension Credit pay, through the higher earnings
    disregard, no consistent state exists: Pension Credit would end the
    award, which would end Pension Credit. The award then stands beside the
    Pension Credit the model works out on it.

    In a year with tax credits, this branch reaches the passport branch
    (pension_credit_with_passported_tax_credits), and the passport branch
    reaches this one. A branch reads the inputs its parents set, so a branch
    of either keeps both.
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
        "Neither the claimant nor the other member of the couple may be entitled to "
        "State Pension Credit (Sch 1 para 6(1)(c) and (d)). Pension Credit reads the "
        "couple's award, so the screen reads the Pension Credit the couple would get "
        "with no income-related ESA in the family "
        "(pension_credit_without_income_related_esa), which counts the claim "
        "(would_claim_pc) and an entered award, and bars the couple's claim where it "
        "pays more than nil. It works that out only for a population in which some "
        "couple's claim passes the other tests and the couple meets the Pension "
        "Credit age conditions (meets_pension_credit_age_conditions) and would claim, "
        "and bars only such a couple. Where Pension Credit pays nothing without the "
        "award but pays with "
        "it, through the higher earnings disregard the award brings (SPC Regs 2002 "
        "Sch VI para 4(1)(a)(vii)), no consistent state exists, and the family gets "
        "both. The couple's Pension Credit bars only the couple's claim, not that of "
        "a member who claims in their own right. The claimant must not engage in "
        "remunerative work (para 6(1)(e); esa_income_claimant_remunerative_work). The "
        "other member of the couple must not engage in remunerative work (para "
        "6(1)(f)): paid work of 24 hours a week or more (ESA Regs 2008 reg 42(1)), "
        "subject to the existing carer exception (reg 43(2)(c); IS Regs 1987 Sch 1B "
        "para 4), which the model reads as is_carer_for_benefits. Assessable capital "
        "must remain within the existing limit (para 6(1)(b); reg 110). The model "
        "applies neither para 6(1)(g) (receiving education) nor the other member's "
        "income-based JSA under para 6(1)(d). The Welfare Reform Act (Northern "
        "Ireland) 2007 sets the same conditions in s.1(3)(c) and Sch 1 para 6(1)(c) "
        "and (d), but its s.1(6) takes pensionable age from the Pensions (Northern "
        "Ireland) Order 1995 Sch 2 para 1, not the Pensions Act 1995 Sch 4 para 1. "
        "The two give the same pensionable age for every date of birth, so one rule "
        "covers the UK. The aggregate esa_income uses this screen for its original "
        "couple's part; each outside reporter's claim is paid separately on their own "
        "existing work/capital screen, pensionable age and tariff. The benefit unit's "
        "capital is an explicit proxy for unobserved outside-claim capital. Reports "
        "whose own award is closed are excluded before choosing candidates; ESA also "
        "excludes the couple's reports on a UC claim. This variable's candidate rules "
        "are unchanged by the separate aggregation."
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
        # WRA 2007 s.1(3)(c): the claimant "has not reached pensionable age",
        # which s.1(6) takes from Pensions Act 1995 Sch 4 para 1, so a man
        # born before 6 December 1953 reaches it at 65.
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
        # Sch 1 para 6(1)(c) and (d): the claimant is not entitled to State
        # Pension Credit, nor is the other member of the couple. Pension
        # Credit reads the couple's award, so this reads the couple's Pension
        # Credit without it, for a couple whose claim passes the other tests and
        # that meets the Pension Credit age conditions and would claim, and
        # only where some couple does. The couple's Pension Credit does not
        # bar a member who claims in their own right.
        could_be_on_pension_credit = (
            benunit.any(passes & claimant_or_partner)
            & within_capital
            & benunit("meets_pension_credit_age_conditions", period)
            & benunit("would_claim_pc", period)
        )
        on_pension_credit = could_be_on_pension_credit
        if could_be_on_pension_credit.any():
            on_pension_credit = could_be_on_pension_credit & (
                pension_credit_without_income_related_esa(benunit, period) > 0
            )
        pension_credit_bars = claimant_or_partner & benunit.project(on_pension_credit)
        return benunit.any(passes & ~pension_credit_bars) & within_capital

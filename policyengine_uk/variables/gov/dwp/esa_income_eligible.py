from policyengine_uk.model_api import *


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
        "couple's income-related ESA, so the model cannot read the Pension Credit "
        "award here. As for Income Support (income_support_eligible), it takes the "
        "couple to be on Pension Credit where the couple meets the Pension Credit age "
        "conditions (meets_pension_credit_age_conditions) and would claim it "
        "(would_claim_pc). That leaves out Pension Credit's means test, so the screen "
        "also fails for a couple that test would refuse. The couple's Pension Credit "
        "bars only the couple's claim, not that of a member who claims in their own "
        "right. The claimant must not engage in remunerative work (para 6(1)(e); "
        "esa_income_claimant_remunerative_work). The other member of the couple must "
        "not engage in remunerative work (para 6(1)(f)): paid work of 24 hours a week "
        "or more (ESA Regs 2008 reg 42(1)), subject to the existing carer exception "
        "(reg 43(2)(c); IS Regs 1987 Sch 1B para 4), which the model reads as "
        "is_carer_for_benefits. Assessable capital must remain within the existing "
        "limit (para 6(1)(b); reg 110). The model applies neither para 6(1)(g) "
        "(receiving education) nor the other member's income-based JSA under para "
        "6(1)(d). The Welfare Reform Act (Northern Ireland) 2007 sets the same "
        "conditions in the same words, and Northern Ireland's pensionable age "
        "(Pensions (Northern Ireland) Order 1995 Sch 2 para 1) follows the same "
        "timetable, so one rule covers the UK. The aggregate esa_income uses this "
        "screen for its original couple's part; each outside reporter's claim is paid "
        "separately on their own existing work/capital screen, pensionable age and "
        "tariff. The benefit unit's capital is an explicit proxy for unobserved "
        "outside-claim capital. Reports whose own award is closed are excluded before "
        "choosing candidates; ESA also excludes the couple's reports on a UC claim. "
        "This variable's candidate rules are unchanged by the separate aggregation."
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
        # Sch 1 para 6(1)(c) and (d): the claimant is not entitled to State
        # Pension Credit, nor is the other member of the couple. Reading the
        # Pension Credit amount here would be circular: its higher earnings
        # disregard reads this award (SPC Regs 2002 Sch VI para 4(1)(a)(vii)),
        # and so does the working tax credit income test (TCA 2002 s.7(2)),
        # and working tax credit counts as Pension Credit income. As
        # income_support_eligible does for SSCBA 1992 s.124(1)(g), the couple
        # is taken to be on Pension Credit where it meets the Pension Credit
        # age conditions and would claim it. That leaves out the means test: a
        # couple Pension Credit's means test would refuse is still taken to be
        # on it. A family that left the Pension Credit route when DWP moved it
        # to Universal Credit claims Universal Credit, which already ends the
        # couple's award (esa_income_report_closed). The couple's Pension
        # Credit does not bar a member who claims in their own right.
        on_pension_credit = benunit(
            "meets_pension_credit_age_conditions", period
        ) & benunit("would_claim_pc", period)
        pension_credit_bars = claimant_or_partner & benunit.project(on_pension_credit)
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
        claimant = (
            candidate
            & ~pensionable_age
            & ~pension_credit_bars
            & ~claimant_works
            & ~other_member_works
        )
        return benunit.any(claimant) & (capital <= ESA.capital.limit)

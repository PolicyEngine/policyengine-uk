from policyengine_uk.model_api import *


class esa_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether a reported income-related ESA award passes the capital and work tests"
    )
    documentation = (
        "Bounded work/capital screen for reported income-related ESA, not a full "
        "entitlement model. When an original claimant or partner reports an open "
        "award, only they are candidate claimants; otherwise other open reporters "
        "are candidates. The claimant must not engage in remunerative work (Welfare "
        "Reform Act 2007 Sch 1 para 6(1)(e); "
        "esa_income_claimant_remunerative_work). The other member of the couple "
        "must not engage in remunerative work (para 6(1)(f)): paid work of 24 hours "
        "a week or more (ESA Regs 2008 reg 42(1)), subject to the existing carer "
        "exception (reg 43(2)(c); IS Regs 1987 Sch 1B para 4), which the model "
        "reads as is_carer_for_benefits. Assessable capital must remain within the "
        "existing limit (para 6(1)(b); reg 110). The aggregate esa_income uses this "
        "screen for its original couple's part; each outside reporter's claim is "
        "paid separately on their own existing work/capital screen and tariff. The "
        "benefit unit's capital is an explicit proxy for unobserved outside-claim "
        "capital. Reports whose own award is closed are excluded before choosing "
        "candidates; ESA also excludes the couple's reports on a UC claim. This "
        "variable's candidate rules are unchanged by the separate aggregation."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2007/5/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/41",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/42",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/43",
        "https://www.legislation.gov.uk/uksi/2008/794/regulation/110",
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
        claimant = candidate & ~claimant_works & ~other_member_works
        return benunit.any(claimant) & (capital <= ESA.capital.limit)

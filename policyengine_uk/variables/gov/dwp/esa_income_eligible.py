from policyengine_uk.model_api import *


class esa_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether a reported income-related ESA award passes the capital and work tests"
    )
    documentation = (
        "Bounded screen applied to reported income-related ESA awards: the "
        "capital test (Welfare Reform Act 2007 Sch 1 para 6(1)(b); ESA Regs "
        "2008 reg 110) and the remunerative work conditions. The claimant "
        "must not be engaged in remunerative work (para 6(1)(e); "
        "esa_income_claimant_remunerative_work), and must not be a member of "
        "a couple the other member of which is (para 6(1)(f)): paid work of "
        "24 hours a week or more (reg 42(1)), unless the partner is a carer "
        "within IS Regs 1987 Sch 1B para 4 (reg 43(2)(c)), which the model "
        "reads as is_carer_for_benefits. The claimant is a member who "
        "reports the award, tested against the other member of the couple. "
        "When the claimant or partner reports one, only they are candidates: "
        "a member outside the family, such as a non-dependent adult, claims "
        "in their own right, and is tested on their own work only when "
        "neither the claimant nor the partner reports an award. This one "
        "screen decides the benefit unit's award (esa_income) on every report "
        "in it, so when the claimant or partner reports, another member's "
        "report is paid or not with their claim. Whether that member is on "
        "the award themselves (is_on_income_related_esa) is tested on their "
        "own claim. This is not a full entitlement model."
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
        reports_award = person("esa_income_reported", period) > 0
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

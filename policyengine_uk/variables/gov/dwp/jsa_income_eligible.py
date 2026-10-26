from policyengine_uk.model_api import *


class jsa_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether a reported income-based JSA award passes the capital and work tests"
    )
    documentation = (
        "Bounded work/capital screen for reported income-based JSA, not a "
        "full entitlement model. When an original claimant or partner reports "
        "an open award, only they are candidate claimants; otherwise other "
        "open reporters are candidates. The existing rules require that "
        "the reporting claimant must work less than16hours and the other member of the couple less than24hours, retaining the existing joint-claim exception. "
        "Assessable capital must remain within the existing limit. The "
        "aggregate jsa_income uses this screen for its original couple's "
        "part; each outside reporter's claim is paid separately on their own "
        "existing work/capital screen and tariff. The benefit unit's capital "
        "is an explicit proxy for unobserved outside-claim capital. Reports "
        "whose own award is closed are excluded before choosing candidates; "
        "ESA also excludes the couple's reports on a UC claim. This variable's "
        "candidate rules are unchanged by the separate aggregation."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1995/18/section/1",
        "https://www.legislation.gov.uk/ukpga/1995/18/section/3",
        "https://www.legislation.gov.uk/ukpga/1995/18/section/13",
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/3E",
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/51",
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/107",
    )

    def formula(benunit, period, parameters):
        JSA = parameters(period).gov.dwp.JSA
        person = benunit.members
        capital = benunit("jsa_income_assessable_capital", period)
        reports_award = (person("jsa_income_reported", period) > 0) & ~person(
            "person_legacy_benefits_closed", period
        )
        claimant_or_partner = person("is_claimant_or_partner", period)
        # The candidate claimants: the claimant or partner who reports the
        # award, or, if neither does, whoever in the benefit unit does.
        couple_reports = benunit.any(reports_award & claimant_or_partner)
        candidate = reports_award & (
            claimant_or_partner | ~benunit.project(couple_reports)
        )
        WORK = JSA.remunerative_work
        hours = person("jsa_remunerative_work_hours", period)
        # s.1(2)(e) and reg 51(1)(a): 16 hours for the claimant.
        works_as_claimant = hours >= WORK.claimant_hours
        # s.3(1)(e) and reg 51(1)(b): 24 hours for the other member of the
        # couple, joint claim or not (reg 3E(2)(g)).
        works_as_partner = claimant_or_partner & (hours >= WORK.partner_hours)
        other_member_works = claimant_or_partner & (
            (benunit.project(benunit.sum(works_as_partner)) - works_as_partner) > 0
        )
        claimant = candidate & ~works_as_claimant & ~other_member_works
        return benunit.any(claimant) & (capital <= JSA.income.capital.limit)

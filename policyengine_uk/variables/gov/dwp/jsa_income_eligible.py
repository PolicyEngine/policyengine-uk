from policyengine_uk.model_api import *


class jsa_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether a reported income-based JSA award passes the capital and work tests"
    )
    documentation = (
        "Bounded screen applied to reported income-based JSA awards: the "
        "capital test (Jobseekers Act 1995 s.13(1) and (2A); JSA Regs 1996 "
        "reg 107) and the remunerative work conditions. The claimant must not "
        "be engaged in remunerative work, paid work of 16 hours a week or "
        "more (s.1(2)(e); reg 51(1)(a)), and the claimant's partner must not "
        "work 24 hours or more (s.3(1)(e); reg 51(1)(b)). A couple without "
        "children of the prescribed description claim jointly, and each of "
        "them is then a claimant held to 16 hours (s.1(2B)(b), s.35(1)). But "
        "a member of a joint-claim couple may claim alone when the other "
        "works 16 hours or more but less than 24 (reg 3E(1) and (2)(g), since "
        "joint claims began on 19 March 2001), and is then tested under s.3, "
        "so an award survives in either case unless the other member works "
        "24 hours or more. The JSA regulations do not take a carer out of "
        "remunerative work for unrelated paid work. The claimant is a member "
        "who reports the award. When the claimant or partner reports one, "
        "only they are candidates: a member outside the family, such as a "
        "non-dependent adult, claims in their own right, and is tested on "
        "their own work only when neither the claimant nor the partner "
        "reports an award. This one screen decides the benefit unit's award "
        "(jsa_income) on every report in it, so when the claimant or partner "
        "reports, another member's report is paid or not with their claim. "
        "Whether that member is on the award themselves "
        "(is_on_income_based_jsa) is tested on their own claim. This is not a "
        "full entitlement model."
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
        reports_award = person("jsa_income_reported", period) > 0
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

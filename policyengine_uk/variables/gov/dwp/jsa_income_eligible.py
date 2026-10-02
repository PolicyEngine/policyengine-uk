from policyengine_uk.model_api import *


class jsa_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether a reported income-based JSA award passes the capital and work tests"
    )
    documentation = (
        "Bounded screen applied to reported income-based JSA awards: the "
        "capital test (Jobseekers Act 1995 s.13(1) and (2A); JSA Regs 1996 reg 107) "
        "and the remunerative work conditions. The claimant must not be "
        "engaged in remunerative work, paid work of 16 hours a week or more "
        "(s.1(2)(e); reg 51(1)(a)). In a joint-claim couple both members are "
        "claimants, so neither may work 16 hours (s.1(2B)(b)); otherwise the "
        "claimant's partner must not work 24 hours or more (s.3(1)(e); reg "
        "51(1)(b)). Unlike Income Support and income-related ESA, the JSA "
        "regulations do not take a carer out of remunerative work. The "
        "claimant is a member who reports the award. When the claimant or "
        "partner reports one, only they are candidates: a member outside the "
        "family, such as a non-dependent adult, claims in their own right, "
        "and is tested on their own work only when neither the claimant nor "
        "the partner reports an award. This is not a full entitlement model."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1995/18/section/1",
        "https://www.legislation.gov.uk/ukpga/1995/18/section/3",
        "https://www.legislation.gov.uk/ukpga/1995/18/section/13",
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
        # s.1(2)(e) and reg 51(1)(a): 16 hours for a claimant, including each
        # member of a joint-claim couple.
        works_as_claimant = hours >= WORK.claimant_hours
        # s.3(1)(e) and reg 51(1)(b): 24 hours for the partner, outside a
        # joint claim.
        joint_claim = benunit.project(benunit("is_jsa_joint_claim_couple", period))
        works_as_other_member = claimant_or_partner & where(
            joint_claim, works_as_claimant, hours >= WORK.partner_hours
        )
        other_member_works = claimant_or_partner & (
            (
                benunit.project(benunit.sum(works_as_other_member))
                - works_as_other_member
            )
            > 0
        )
        claimant = candidate & ~works_as_claimant & ~other_member_works
        return benunit.any(claimant) & (capital <= JSA.income.capital.limit)

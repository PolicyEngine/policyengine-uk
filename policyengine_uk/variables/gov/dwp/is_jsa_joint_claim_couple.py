from policyengine_uk.model_api import *


class is_jsa_joint_claim_couple(Variable):
    value_type = bool
    entity = BenUnit
    label = "Joint-claim couple for income-based JSA"
    documentation = (
        "Whether the claimant and partner are a joint-claim couple, who "
        "claim income-based Jobseeker's Allowance together, so that each of "
        "them is a claimant (Jobseekers Act 1995 ss.1(2B) and 35(1)). A "
        "joint-claim couple is a couple with no child or young person in the "
        "family for whom one of them is entitled to Child Benefit (s.1(4)), "
        "nor a child or young person they care for in the circumstances of "
        "JSA Regs 1996 reg 78(4) or (8), at least one of whom is 18 or over "
        "and was born after the prescribed date (reg 3A(1)). Joint claims "
        "began on 19 March 2001. The model reads a child or young person as "
        "a Child Benefit child or qualifying young person in the benefit "
        "unit other than the claimant and partner, including a child placed "
        "with them. The circumstances in which one member of a joint-claim "
        "couple may claim alone (regs 3D and 3E) are not modelled; enter this "
        "variable directly for them."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/1995/18/section/1",
        "https://www.legislation.gov.uk/ukpga/1995/18/section/35",
        "https://www.legislation.gov.uk/uksi/1996/207/regulation/3A",
    )

    def formula(benunit, period, parameters):
        joint_claim = parameters(period).gov.dwp.JSA.income.joint_claim
        if not joint_claim.in_effect:
            return benunit.empty_array() > 0
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        couple = benunit.sum(claimant_or_partner) == 2
        child_or_young_person = (
            person("is_child_or_qualifying_young_person_for_child_benefit", period)
            & ~claimant_or_partner
        )
        prescribed_member = (
            claimant_or_partner
            & (person("age", period) >= 18)
            & (person("birth_year", period) > joint_claim.born_after_year)
        )
        return (
            couple
            & ~benunit.any(child_or_young_person)
            & benunit.any(prescribed_member)
        )

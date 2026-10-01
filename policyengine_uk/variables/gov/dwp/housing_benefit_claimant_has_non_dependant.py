from policyengine_uk.model_api import *


class housing_benefit_claimant_has_non_dependant(Variable):
    value_type = bool
    entity = BenUnit
    label = "Housing Benefit claimant has a non-dependant residing with them"
    documentation = (
        "Whether a non-dependant normally resides with the claimant, which "
        "stops a young individual getting the shared accommodation rate. A "
        "member of the claimant's benefit unit is one if neither the claimant "
        "or partner nor a child or young person (see "
        "is_benefit_unit_non_dependant_for_legacy_benefits). So is the "
        "claimant or partner of another family of the household who is not "
        "liable for rent (see is_non_dependant_of_household_head). A "
        "non-dependant who lives with joint occupiers resides with each of "
        "them, so a family liable for a share of the rent also has the other "
        "liable families' non-dependants, as in "
        "housing_benefit_non_dep_deductions. A boarder or lodger has only "
        "their own family's. Universal Credit has its own test: see "
        "universal_credit_renter_has_non_dependant."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/19",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/3",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # HB Regs 2006 reg 3(1) and (2)(a), (c): a member of the claimant's
        # benefit unit outside the claimant's family. The young person test is
        # Child Benefit's (reg 19), with no separate rule for 16-year-olds: one
        # outside it is a non-dependant, and one within it makes the claimant
        # a lone parent rather than a single claimant (reg 2(1)), so either
        # way the claimant is not a young individual with no non-dependant.
        own_family = person("is_benefit_unit_non_dependant_for_legacy_benefits", period)
        within_benefit_unit = benunit.any(own_family)
        # Reg 3(2)(d)-(e), (4): the claimant or partner of another family who
        # is not liable for rent resides with the household's joint
        # occupiers, as does a non-dependant in a joint occupier's own family
        # (reg 74(5)). A boarder or lodger has no share of the household's
        # rent and lives with neither.
        other_family_claimant = person("is_claimant_or_partner", period) & person(
            "is_non_dependant_of_household_head", period
        )
        member_of_joint_occupier = person.benunit("share_of_household_rent", period) > 0
        resides_with_joint_occupiers = other_family_claimant | (
            own_family & member_of_joint_occupier
        )
        joint_occupier = benunit("share_of_household_rent", period) > 0
        from_joint_occupation = joint_occupier & (
            benunit.max(person.household.sum(resides_with_joint_occupiers)) > 0
        )
        return within_benefit_unit | from_joint_occupation

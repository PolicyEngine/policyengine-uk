from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
    deduction_per_family,
)


class housing_benefit_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "non-dependent deductions"
    documentation = (
        "Deductions for the non-dependants residing with the claimant: "
        "members of other families of the household who are not liable for "
        "rent, and members of a family liable for the rent who are not its "
        "claimant, partner or a child or young person. One deduction for "
        "each non-dependant couple, the higher of the two members' amounts, "
        "and one for each other non-dependant. Each is apportioned between "
        "joint occupiers by their shares of the rent, whichever family they "
        "are in; a boarder or lodger also bears the whole deduction for a "
        "non-dependant in its own benefit unit. None if the claimant or "
        "partner is exempt. The model reads a boarder or lodger as outside "
        "the joint occupiers of reg 74(5), which apportions a deduction by "
        "the number of joint occupiers and their shares of the payments, the "
        "factors reg 12(5) uses for rent. DWP's Housing Benefit guidance "
        "describes joint occupiers as people in one home who are each liable "
        "for their occupation and divides the rent between them (A4 paras "
        "4.1920-4.1921), applies reg 74(5) to joint tenants (LHA guidance "
        "para 2.110), keeps joint occupiers, sub-tenants and boarders apart "
        "(C1 paras 1.185 and 1.203) and counts a sub-tenant's payments as the "
        "claimant's income (C1 para 1.205), so the householder's rent and the "
        "lodger's charge have no common total to divide. The 1987 regulations "
        "also put joint occupiers and people liable to pay the claimant in "
        "separate limbs of reg 3(2). No regulation defines a joint occupier "
        "and we know of no decision on the point, so the reading is a "
        "qualified one. Under it, a non-dependant in a claiming lodger's own "
        "benefit unit costs the householder and the lodger one whole "
        "deduction each. Apportioning it between them, or excluding the "
        "lodger's household from the householder's non-dependants as C1 para "
        "1.185 does, would charge it once."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/12",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/uksi/1987/1971/regulation/3/made",
        "https://assets.publishing.service.gov.uk/media/5a7ce2b840f0b6629523c64c/hbgm-a5-calculating-benefit.pdf",
        "https://assets.publishing.service.gov.uk/media/5a7bac56e5274a7202e18aeb/hbgm-a4-eligible-rent.pdf",
        "https://assets.publishing.service.gov.uk/media/5a7b97bc40f0b645ba3c550e/hbgm-c1-aggregation-of-needs.pdf",
        "https://assets.publishing.service.gov.uk/media/5a758238ed915d6faf2b38a2/lha-guidance-manual.pdf",
    )

    def formula(benunit, period, parameters):
        # The council deducts for non-dependants residing with the claimant
        # (HB Regs 2006 reg 74; HB (SPC) Regs 2006 reg 55). Joint occupiers,
        # boarders, lodgers and the landlord's household are not
        # non-dependants (reg 3(2)(d)-(e), 3(4)). For a couple the council deducts once,
        # the higher amount (reg 74(3)). For a non-dependant of more than one joint
        # occupier, the council apportions the deduction by their shares of the
        # payments (reg 74(5); SPC reg 55(5)), so each family liable for the
        # household's rent bears its share; a boarder or lodger bears none of it.
        # A family bearing a share is a joint occupier, never another family's
        # non-dependant, even where the rent is nil and so the family is not
        # benunit_is_rent_liable.
        person = benunit.members
        deductions = person("household_benefits_individual_non_dep_deduction", period)
        in_joint_occupier_family = person.benunit("share_of_household_rent", period) > 0
        other_family = (
            person("is_non_dependant_of_household_head", period)
            & ~in_joint_occupier_family
        )
        # A member of a rent-liable family who is not in its claimant's
        # family under reg 3(2)(a) and (c) is a non-dependant too. That takes
        # in a boarder's or lodger's adult son, whom other_family also counts:
        # what a family pays the householder makes it rent-liable here.
        in_unit = person("is_benefit_unit_non_dependant_for_legacy_benefits", period)
        rent_liable = person.benunit("benunit_is_rent_liable", period)
        own_family = in_unit & (~other_family | rent_liable)
        # A non-dependant normally resides with each joint occupier (reg 3(1)
        # and (4)), whichever family they belong to: another family's adult,
        # a joint occupier's own adult son, or a boarder's or lodger's (reg
        # 3(2)(e)(i) excludes only the person liable to pay the claimant).
        # A couple pays one deduction, the higher (reg 74(3)), and each other
        # non-dependant separately, counted once per family. One who is a
        # non-dependant of more than one joint occupier is apportioned
        # between them by their shares of the payments (reg 74(5); SPC reg
        # 55(5)).
        family_amount = deduction_per_family(
            benunit, period, deductions * (other_family | own_family), False
        )
        counted = person("is_benunit_head", period) * benunit.project(family_amount)
        share = benunit("share_of_household_rent", period)
        from_joint_occupiers = share * benunit.max(person.household.sum(counted))
        # A boarder or lodger is not a joint occupier with the householder,
        # so it also bears the whole deduction for a non-dependant in its own
        # benefit unit. The model charges it for no one else.
        joint_occupier = share > 0
        from_own_family = where(joint_occupier, 0, benunit.sum(deductions * own_family))
        claimant_exempt = benunit(
            "housing_benefit_non_dep_deductions_claimant_exempt", period
        )
        return where(claimant_exempt, 0, from_joint_occupiers + from_own_family)

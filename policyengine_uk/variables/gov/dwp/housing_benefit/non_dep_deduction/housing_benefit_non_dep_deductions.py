from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
    deduction_per_family,
)


class housing_benefit_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "non-dependent deductions"
    documentation = (
        "Deductions for the claimant's non-dependants: members of other "
        "families of the household who are not liable for rent, and members "
        "of a family liable for the rent who are not its claimant, partner or "
        "a child or young person. Another family's non-dependants pay one "
        "deduction per couple, the higher of the two members' amounts, and "
        "one for each other member, apportioned between joint occupiers by "
        "their shares of the rent. A non-dependant in a family's own benefit "
        "unit is that family's alone, including a boarder's or lodger's. None "
        "if the claimant or partner is exempt."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://assets.publishing.service.gov.uk/media/5a7ce2b840f0b6629523c64c/hbgm-a5-calculating-benefit.pdf",
    )

    def formula(benunit, period, parameters):
        # Deductions are made for non-dependants residing with the claimant
        # (HB Regs 2006 reg 74; HB (SPC) Regs 2006 reg 55). Joint occupiers,
        # boarders, lodgers and the landlord's household are not
        # non-dependants (reg 3(2)(d)-(e), 3(4)).
        person = benunit.members
        deductions = person("household_benefits_individual_non_dep_deduction", period)
        other_family = person("is_non_dependant_of_household_head", period)
        # A member of a rent-liable family who is not in its claimant's
        # family under reg 3(2)(a) and (c) is a non-dependant too.
        own_family = (
            person("is_benefit_unit_non_dependant_for_legacy_benefits", period)
            & ~other_family
        )
        # A non-dependant normally resides with each joint occupier (reg 3(1)
        # and (4)), whichever family they belong to: another family's adult,
        # a joint occupier's own adult son, or a boarder's or lodger's (reg
        # 3(2)(e)(i) excludes only the person liable to pay the claimant).
        # One deduction for a non-dependant couple, the higher (reg 74(3)),
        # and one for each other non-dependant, counted once per family. One
        # who is a non-dependant of more than one joint occupier is
        # apportioned between them by their shares of the payments (reg
        # 74(5); SPC reg 55(5)).
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

from policyengine_uk.model_api import *


class housing_benefit_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "non-dependent deductions"
    documentation = (
        "Deductions for the claimant's non-dependants: members of other "
        "families of the household who are not liable for rent, and members "
        "of a family liable for the rent who are not its claimant, partner or "
        "a child or young person. A non-dependant of several joint occupiers "
        "is apportioned between them by their shares of the rent; a boarder "
        "or lodger bears only the non-dependants in their own family."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
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
        # A non-dependant of more than one joint occupier is apportioned
        # between them by their shares of the payments (reg 74(5); SPC reg
        # 55(5)): one living with joint occupiers resides with each of them,
        # whichever family they belong to. A boarder or lodger has no share
        # of the household's rent and bears only their own family's.
        joint_occupier = person.benunit("share_of_household_rent", period) > 0
        shared = other_family | (own_family & joint_occupier)
        share = benunit("share_of_household_rent", period)
        from_joint_occupation = share * benunit.max(
            person.household.sum(deductions * shared)
        )
        from_own_family = benunit.sum(deductions * own_family * ~joint_occupier)
        return from_joint_occupation + from_own_family

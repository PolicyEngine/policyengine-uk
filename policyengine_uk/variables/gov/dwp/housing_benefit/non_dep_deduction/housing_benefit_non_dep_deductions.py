from policyengine_uk.model_api import *


class housing_benefit_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "non-dependent deductions"
    documentation = (
        "Deductions for the claimant's non-dependants: members of other "
        "families of the household who are not liable for rent, and members "
        "of a family liable for the rent who are not its claimant, partner or "
        "a child or young person. A non-dependant from another family is "
        "apportioned between joint occupiers by their shares of the rent. A "
        "non-dependant in a family's own benefit unit is that family's alone, "
        "including a boarder's or lodger's."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://assets.publishing.service.gov.uk/media/5a758238ed915d6faf2b38a2/lha-guidance-manual.pdf#page=33",
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
        # A non-dependant of more than one joint occupier is apportioned
        # between them by their shares of the payments (reg 74(5); SPC reg
        # 55(5)). A member of a joint occupier's own family unit is that
        # occupier's non-dependant only (LHA Guidance Manual 2.093, example
        # 2: a joint tenant's sister "is treated as Sarah's non-dependant"),
        # and "if a person is a non-dependant of only one of the joint
        # occupiers, take the whole of the deduction from that joint
        # occupier's entitlement" (HBGM A5 5.622). Their family bears the
        # whole deduction, whatever its share of the rent; so does a boarder
        # or lodger.
        share = benunit("share_of_household_rent", period)
        from_other_families = share * benunit.max(
            person.household.sum(deductions * other_family)
        )
        from_own_family = benunit.sum(deductions * own_family)
        return from_other_families + from_own_family

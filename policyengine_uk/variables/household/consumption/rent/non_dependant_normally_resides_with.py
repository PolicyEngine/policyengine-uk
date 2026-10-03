from policyengine_uk.model_api import *


class NonDependantResidence(Enum):
    EVERY_JOINT_OCCUPIER = "Every family liable for the household's rent"
    HOUSEHOLD_HEAD_FAMILY = "The household head's family only"
    OTHER_JOINT_OCCUPIERS = (
        "The families sharing the household's rent with the household head's "
        "family only"
    )


class non_dependant_normally_resides_with(Variable):
    value_type = Enum
    possible_values = NonDependantResidence
    default_value = NonDependantResidence.EVERY_JOINT_OCCUPIER
    entity = BenUnit
    label = "Joint occupiers this family's non-dependants normally reside with"
    documentation = (
        "For a family of non-dependants in a household whose rent is shared "
        "by joint occupiers (joint tenants and other sharers of the rent), "
        "which of those joint occupiers the family normally resides with for "
        "Housing Benefit and Council Tax Reduction. This is a question of "
        "fact. A non-dependant who lives with all of them, such as a friend "
        "of two joint tenants, is each one's non-dependant: they count in "
        "each joint tenant's size criteria and their deduction is apportioned "
        "between them. One who lives with only one joint tenant, such as that "
        "tenant's sister, counts only for that tenant, who bears the whole "
        "deduction. The default is every joint occupier. With more than one "
        "family sharing the rent with the household head's family, the third "
        "value covers all of those families together. Where no family shares "
        "the rent, every value means the household head's family. Universal "
        "Credit does not use this input: a non-dependant counts in one Universal "
        "Credit claim only, which the model gives to the household head's "
        "family (see is_non_dependant_of_household_head)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/9",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/8",
        "https://assets.publishing.service.gov.uk/media/5a758238ed915d6faf2b38a2/lha-guidance-manual.pdf#page=33",
    )


def rent_shared_with_another_family(benunit, period):
    """Whether a family other than the household head's shares the
    household's rent (liable_for_share_of_household_rent). The head's family
    is always liable, so the flag on the head's own family means nothing."""
    person = benunit.members
    in_sharer_family = person.benunit(
        "liable_for_share_of_household_rent", period
    ) & ~person.benunit.any(person("is_household_head", period))
    return benunit.any(person.household.any(in_sharer_family))


def _joint_occupiers_by_residence(benunit, period):
    """Pairs of (residence value, whether each family is one of the joint
    occupiers a non-dependant with that value normally resides with)."""
    person = benunit.members
    values = NonDependantResidence
    head_family = benunit.any(person("is_household_head", period))
    sharer = benunit("liable_for_share_of_household_rent", period) & ~head_family
    rent_is_shared = rent_shared_with_another_family(benunit, period)
    return (
        (values.EVERY_JOINT_OCCUPIER, head_family | sharer),
        (values.HOUSEHOLD_HEAD_FAMILY, head_family),
        (values.OTHER_JOINT_OCCUPIERS, where(rent_is_shared, sharer, head_family)),
    )


def _outside_joint_occupiers(benunit, period):
    """Whether each person is outside every family liable for the household's
    rent (the household head's family and the sharers). A joint occupier is
    never a non-dependant of itself or of another joint occupier (HB Regs
    2006 reg 3(2)(a), (d); SI 2012/2885 reg 9(2)(a), (d)), whatever its own
    rent."""
    person = benunit.members
    head_family = person.benunit.any(person("is_household_head", period))
    sharer = person.benunit("liable_for_share_of_household_rent", period)
    return ~head_family & ~sharer


def _household_total_over_families(benunit, period, value, families):
    """For each family, the household total of a family-level ``value`` over
    the families marked by ``families``."""
    person = benunit.members
    on_head = person("is_benunit_head", period)
    return benunit.max(
        person.household.sum(on_head * benunit.project(value * families))
    )


def non_dependants_residing_with(benunit, period, non_dependant):
    """For each family, the sum of ``non_dependant`` (a count or weight for
    each member of a non-dependant family, zero for anyone else) over the
    household's people who normally reside with it under
    non_dependant_normally_resides_with. Members of the joint occupiers'
    families are never counted."""
    person = benunit.members
    residence = person.benunit("non_dependant_normally_resides_with", period)
    source = non_dependant * _outside_joint_occupiers(benunit, period)
    count = 0
    for value, joint_occupier in _joint_occupiers_by_residence(benunit, period):
        in_household = benunit.max(person.household.sum(source * (residence == value)))
        count = count + joint_occupier * in_household
    return count


def apportioned_non_dependant_deductions(
    benunit, period, deductions, equally, every_joint_occupier_part
):
    """For each family, its part of the deductions for the household's
    non-dependants (``deductions``, one amount per person and zero for anyone
    who is not a non-dependant; members of the joint occupiers' families are
    never counted), each split between the joint occupiers the non-dependant
    normally resides with.

    For a non-dependant of every joint occupier, each family's part is
    ``every_joint_occupier_part``: its share of the rent for Housing Benefit
    (share_of_household_rent) and its joint liability share for Council Tax
    Reduction (council_tax_reduction_joint_liability_share), as before.

    For a non-dependant of some of them, with ``equally`` false (Housing
    Benefit, reg 74(5)), each joint occupier's part is its share of the rent
    over the shares of all of them, or its people liable for the rent over
    theirs where those shares sum to zero; with ``equally`` true (Council Tax
    Reduction, SI 2012/2885 Sch 1 para 8(5)), each part is one over the
    number of people liable among them, and the whole where only the family
    is liable. A family that is a non-dependant's only host, a couple
    included, bears the whole deduction: the model cannot tell whether both
    partners are named tenants liable under LGFA 1992 s.6 (when the literal
    para 8(5) would split it between them) or liable only as spouses (s.9).

    Where no family other than the household head's shares the rent, every
    residence value means the head's family alone, which takes
    ``every_joint_occupier_part``.
    """
    person = benunit.members
    residence = person.benunit("non_dependant_normally_resides_with", period)
    source = deductions * _outside_joint_occupiers(benunit, period)
    # Without another family sharing the rent, every value means the
    # household head's family alone, so each takes the caller's part.
    rent_is_shared = rent_shared_with_another_family(benunit, period)
    liable = person("is_liable_for_household_rent", period)
    liable_in_family = benunit.sum(liable)
    share = benunit("share_of_household_rent", period)
    values = NonDependantResidence
    total = 0
    for value, joint_occupier in _joint_occupiers_by_residence(benunit, period):
        liable_in_joint_occupiers = benunit.max(
            person.household.sum(liable & benunit.project(joint_occupier))
        )
        if value == values.EVERY_JOINT_OCCUPIER:
            part = every_joint_occupier_part
        elif equally:
            part = where(
                liable_in_joint_occupiers > liable_in_family,
                1 / max_(liable_in_joint_occupiers, 1),
                1,
            )
        else:
            share_of_joint_occupiers = _household_total_over_families(
                benunit, period, share, joint_occupier
            )
            part = where(
                share_of_joint_occupiers > 0,
                share
                / where(share_of_joint_occupiers > 0, share_of_joint_occupiers, 1),
                liable_in_family / max_(liable_in_joint_occupiers, 1),
            )
        part = where(rent_is_shared, part, every_joint_occupier_part)
        pool = benunit.max(person.household.sum(source * (residence == value)))
        total = total + joint_occupier * part * pool
    return total

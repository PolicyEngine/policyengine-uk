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


def _joint_occupiers_by_residence(benunit, period):
    """Pairs of (residence value, whether each family is one of the joint
    occupiers a non-dependant with that value normally resides with)."""
    person = benunit.members
    values = NonDependantResidence
    head_family = benunit.any(person("is_household_head", period))
    sharer = benunit("liable_for_share_of_household_rent", period) & ~head_family
    in_sharer_family = person.benunit(
        "liable_for_share_of_household_rent", period
    ) & ~person.benunit.any(person("is_household_head", period))
    rent_is_shared = benunit.any(person.household.any(in_sharer_family))
    return (
        (values.EVERY_JOINT_OCCUPIER, head_family | sharer),
        (values.HOUSEHOLD_HEAD_FAMILY, head_family),
        (values.OTHER_JOINT_OCCUPIERS, where(rent_is_shared, sharer, head_family)),
    )


def non_dependants_residing_with(benunit, period, non_dependant):
    """For each family, the sum of ``non_dependant`` (a count or weight for
    each member of a non-dependant family, zero for anyone else) over the
    household's people who normally reside with it under
    non_dependant_normally_resides_with."""
    person = benunit.members
    residence = person.benunit("non_dependant_normally_resides_with", period)
    count = 0
    for value, joint_occupier in _joint_occupiers_by_residence(benunit, period):
        in_household = benunit.max(
            person.household.sum(non_dependant * (residence == value))
        )
        count = count + joint_occupier * in_household
    return count


def apportioned_non_dependant_deductions(benunit, period, deductions, equally):
    """For each family, its part of the deductions for the household's
    non-dependants (``deductions``, one amount per person and zero for anyone
    who is not a non-dependant), each split between the joint occupiers the
    non-dependant normally resides with.

    With ``equally`` false (Housing Benefit, reg 74(5)), each joint occupier's
    part is its share of the rent among them: the people liable for the rent
    in its family over those in all of them. With ``equally`` true (Council
    Tax Reduction, SI 2012/2885 Sch 1 para 8(5)), each part is one over the
    number of people liable among them, and the whole where only the family
    is liable.
    """
    person = benunit.members
    residence = person.benunit("non_dependant_normally_resides_with", period)
    liable = person("is_liable_for_household_rent", period)
    liable_in_family = benunit.sum(liable)
    total = 0
    for value, joint_occupier in _joint_occupiers_by_residence(benunit, period):
        liable_in_joint_occupiers = benunit.max(
            person.household.sum(liable & benunit.project(joint_occupier))
        )
        if equally:
            part = where(
                liable_in_joint_occupiers > liable_in_family,
                1 / max_(liable_in_joint_occupiers, 1),
                1,
            )
        else:
            part = liable_in_family / max_(liable_in_joint_occupiers, 1)
        pool = benunit.max(person.household.sum(deductions * (residence == value)))
        total = total + joint_occupier * part * pool
    return total

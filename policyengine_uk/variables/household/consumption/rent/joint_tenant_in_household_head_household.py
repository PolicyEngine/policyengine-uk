from policyengine_uk.model_api import *


class joint_tenant_in_household_head_household(Variable):
    value_type = bool
    entity = BenUnit
    label = "Joint tenant in the household head's household"
    documentation = (
        "Whether this family, which shares liability for the household's rent "
        "with the household head's family (see "
        "liable_for_share_of_household_rent), forms a single household with "
        "the head's family: for example, an adult son who is a joint tenant "
        "with his mother and keeps a common household with her. This is a "
        "question of fact. Housing Benefit counts a joint tenant who is a "
        "member of the claimant's household as an occupier in the size "
        "criteria, but not one who is not, so the families of a single "
        "household count each other, and all of them have the same "
        "occupiers. The default is a separate household. The input has no "
        "effect for a family that does not share the rent, and Universal "
        "Credit does not use it."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/13D",
        "https://assets.publishing.service.gov.uk/media/5a758238ed915d6faf2b38a2/lha-guidance-manual.pdf#page=26",
        "https://assets.publishing.service.gov.uk/media/5a758238ed915d6faf2b38a2/lha-guidance-manual.pdf#page=34",
    )


def in_joint_tenants_single_household(benunit, period):
    """For each family, whether it belongs to a single household of two or
    more joint occupiers: the household head's family and every family
    sharing the rent that forms a single household with it
    (joint_tenant_in_household_head_household), where there is at least one
    such family."""
    person = benunit.members
    in_head_family = person.benunit.any(person("is_household_head", period))
    in_joining_family = (
        person.benunit("joint_tenant_in_household_head_household", period)
        & person.benunit("liable_for_share_of_household_rent", period)
        & ~in_head_family
    )
    head_family = benunit.any(in_head_family)
    someone_joins = benunit.any(person.household.any(in_joining_family))
    return benunit.any(in_joining_family) | (head_family & someone_joins)

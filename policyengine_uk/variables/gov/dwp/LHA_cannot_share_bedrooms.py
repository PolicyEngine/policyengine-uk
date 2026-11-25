from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_allowed_bedrooms import (
    universal_credit_child_bedrooms,
)


class LHA_cannot_share_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit bedrooms for children and couples who cannot share"
    documentation = (
        "Additional bedrooms in the Universal Credit size criteria under the "
        "disabled child and disabled person conditions. Disabled child "
        "condition: each child in the renter's extended benefit unit who "
        "cannot share a bedroom because of disability (see "
        "is_child_who_cannot_share_bedroom) has a bedroom of their own and "
        "the other children share as usual; the additional bedrooms are as "
        "many as that takes beyond the rooms the children would otherwise "
        "need, so none where such a child would not otherwise share. Where "
        "several such children could each have a room alone but not all at "
        "once, the model gives them all their own rooms. That is its reading "
        "of para 12(8) ('each such child has their own bedroom'), as of HB "
        "reg 13D(3)(ba); the DWP guidance's examples do not settle the case. "
        "Disabled person "
        "condition: one bedroom if the renter or a joint renter cannot share "
        "a bedroom with the other because of disability (see "
        "is_member_of_couple_who_cannot_share_bedroom). The condition needs "
        "a joint renter to share with (para 12(6A)), and joint renters are "
        "joint claimants (para 1(2)). So the bedroom needs two Universal "
        "Credit claimants (is_uc_single_or_joint_claimant) and no single "
        "claim (uc_member_of_couple_claims_as_single_person, which can also "
        "be supplied). A member of a couple who claims as a single person "
        "(UC Regs 2013 reg 3(3)) has no joint claimant, so no joint renter, "
        "and gets no such bedroom. That includes a claimant over the "
        "qualifying age for State Pension Credit on the SI 2014/1230 reg 60A "
        "route, whom the single-claim flag does not mark. Housing Benefit "
        "has no such claim and still gives "
        "the couple a bedroom each (see "
        "housing_benefit_LHA_cannot_share_bedrooms). Unlike Housing "
        "Benefit, Universal Credit does not require the home to have the "
        "extra bedroom."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/10",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        # UC Regs 2013 Sch 4 para 12(6) and (8): as many additional bedrooms
        # as are necessary for each child in the extended benefit unit who
        # would otherwise be expected to share, and is not reasonably able
        # to, to have their own bedroom. The children are those the size
        # criteria count (universal_credit_child_bedrooms).
        cannot_share = person("is_child_who_cannot_share_bedroom", period)
        disabled_child_rooms = universal_credit_child_bedrooms(
            benunit, period, cannot_share
        ) - universal_credit_child_bedrooms(benunit, period)
        # Para 12(6A) and (9)(d): one additional bedroom if the renter or a
        # joint renter satisfies the disabled person condition. The renter
        # must otherwise be expected to share a bedroom "with a joint
        # renter", and para 1(2) defines joint renters as joint claimants
        # to whom reg 26(2) applies. A member of a couple who claims as a
        # single person (reg 3(3)) has no joint claimant, so no joint renter
        # and no such bedroom. Two tests mark that claim. The claimant count
        # covers every single claim the model derives, including a claimant
        # over the State Pension Credit age on the SI 2014/1230 reg 60A
        # route, whom uc_member_of_couple_claims_as_single_person leaves
        # false. The flag covers a single claim supplied as an input. The
        # mask is applied here rather than in
        # is_member_of_couple_who_cannot_share_bedroom, which Housing
        # Benefit also reads: Housing Benefit has no single claim.
        couple_member_cannot_share = benunit.any(
            person("is_member_of_couple_who_cannot_share_bedroom", period)
        )
        claims_as_single_person = benunit(
            "uc_member_of_couple_claims_as_single_person", period
        )
        joint_claimants = (
            benunit.sum(person("is_uc_single_or_joint_claimant", period)) == 2
        )
        disabled_person_room = (
            couple_member_cannot_share & ~claims_as_single_person & joint_claimants
        )
        return disabled_child_rooms + 1.0 * disabled_person_room

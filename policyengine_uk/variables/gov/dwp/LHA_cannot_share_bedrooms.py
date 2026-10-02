from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_allowed_bedrooms import (
    bedrooms_for_children,
    universal_credit_size_criteria_people,
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
        "once, the model gives them all their own rooms. Disabled person "
        "condition: one bedroom if the renter or a joint renter cannot share "
        "a bedroom with the other because of disability (see "
        "is_member_of_couple_who_cannot_share_bedroom). Unlike Housing "
        "Benefit, Universal Credit does not require the home to have the "
        "extra bedroom."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/12",
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/10",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        responsible, non_dependant = universal_credit_size_criteria_people(
            benunit, period
        )

        def children(cannot_share=None):
            return bedrooms_for_children(
                benunit,
                period,
                own_child=responsible,
                other_child=non_dependant,
                cannot_share=cannot_share,
            )

        # UC Regs 2013 Sch 4 para 12(6) and (8): as many additional bedrooms
        # as are necessary for each child in the extended benefit unit who
        # would otherwise be expected to share, and is not reasonably able
        # to, to have their own bedroom.
        cannot_share = person("is_child_who_cannot_share_bedroom", period)
        disabled_child_rooms = children(cannot_share) - children()
        # Para 12(6A) and (9)(d): one additional bedroom if the renter or a
        # joint renter satisfies the disabled person condition.
        disabled_person_room = benunit.any(
            person("is_member_of_couple_who_cannot_share_bedroom", period)
        )
        return disabled_child_rooms + 1.0 * disabled_person_room

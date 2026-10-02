from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_allowed_bedrooms import (
    bedrooms_for_children,
)
from policyengine_uk.variables.gov.dwp.housing_benefit_LHA_allowed_bedrooms import (
    housing_benefit_bedrooms_if_able_to_share,
    housing_benefit_occupiers,
)


class housing_benefit_LHA_cannot_share_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit bedrooms for children and couples who cannot share"
    documentation = (
        "Bedrooms in the Housing Benefit size criteria beyond those the "
        "claimant would have if every occupier could share. Each occupier "
        "child who cannot share a bedroom because of disability (see "
        "is_child_who_cannot_share_bedroom) has a room of their own and the "
        "other children share as usual, so there is no extra room where such "
        "a child would not otherwise share. A couple of occupiers, the "
        "claimant's own or another family's, has a bedroom each instead of "
        "one between them if either member cannot share with the other (see "
        "is_member_of_couple_who_cannot_share_bedroom). These bedrooms count "
        "only so far as the dwelling has bedrooms beyond the claimant's "
        "entitlement if everyone could share, including the additional "
        "bedrooms for overnight care and qualifying parents or carers. The "
        "dwelling's bedrooms are read from num_bedrooms; where that is 0, "
        "meaning not reported (the Family Resources Survey records at least "
        "one bedroom for every household, and the released enhanced FRS does "
        "not carry it), the model assumes the dwelling has the bedrooms."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/2",
        "https://www.legislation.gov.uk/uksi/2017/213/made",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        occupier, other_occupier = housing_benefit_occupiers(benunit, period)

        def children(cannot_share=None):
            return bedrooms_for_children(
                benunit,
                period,
                own_child=occupier,
                other_child=other_occupier,
                cannot_share=cannot_share,
            )

        # HB Regs 2006 reg 13D(3)(ba): a child who cannot share a bedroom is
        # a category of their own, ahead of the pairs in (c) and (d).
        cannot_share = person("is_child_who_cannot_share_bedroom", period)
        child_rooms = children(cannot_share) - children()
        # Reg 13D(3)(za) and (zb), ahead of (a): each member of a couple one
        # of whom cannot share has their own bedroom, so the couple has two
        # rather than one. The claimant's own couple:
        member = person("is_member_of_couple_who_cannot_share_bedroom", period)
        own_couple_room = benunit.any(member & occupier)
        # Occupier couples of other families, counted for the household
        # head's family (see housing_benefit_bedrooms_if_able_to_share): one
        # further bedroom per couple, however many of its members qualify.
        aged_16_or_over = person("age", period) >= 16
        counted = (
            other_occupier & aged_16_or_over & person("is_claimant_or_partner", period)
        )
        couple = (person.benunit.sum(counted) == 2) & person.benunit(
            "is_couple", period
        )
        qualifying = counted & couple & member
        per_couple = qualifying / max_(person.benunit.sum(qualifying), 1)
        is_head_family = benunit.any(person("is_household_head", period))
        other_couple_rooms = is_head_family * benunit.max(
            person.household.sum(per_couple)
        )
        extra = child_rooms + 1.0 * own_couple_room + other_couple_rooms
        # Reg 13D(3), closing words: only if the dwelling has a bedroom
        # additional to those to which the claimant would be entitled if the
        # child or the member of the couple were able to share.
        able_to_share = housing_benefit_bedrooms_if_able_to_share(benunit, period)
        bedrooms = benunit.max(person.household("num_bedrooms", period))
        spare = max_(bedrooms - able_to_share, 0)
        return where(bedrooms > 0, min_(extra, spare), extra)

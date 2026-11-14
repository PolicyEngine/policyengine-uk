from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit_LHA_allowed_bedrooms import (
    housing_benefit_bedrooms_if_able_to_share,
    housing_benefit_child_bedrooms,
    housing_benefit_occupiers_total,
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
        occupiers_total = housing_benefit_occupiers_total(benunit, period)
        # HB Regs 2006 reg 13D(3)(ba): a child who cannot share a bedroom is
        # a category of their own, ahead of the pairs in (c) and (d).
        cannot_share = person("is_child_who_cannot_share_bedroom", period)
        child_rooms = housing_benefit_child_bedrooms(
            benunit, period, cannot_share
        ) - housing_benefit_child_bedrooms(benunit, period)
        # Reg 13D(3)(za) and (zb), ahead of (a): each member of a couple one
        # of whom cannot share has their own bedroom, so the couple has two
        # rather than one. This holds for every couple of occupiers, the
        # claimant's own and those of the other families the claim counts
        # (see housing_benefit_occupiers_total): one further bedroom per
        # couple, however many of its members qualify. As in the (a) bedroom,
        # a family counts as a couple only where both members are present.
        claimant_or_partner = person("is_claimant_or_partner", period)
        couple = (person.benunit.sum(claimant_or_partner) == 2) & person.benunit(
            "is_couple", period
        )
        member = person("is_member_of_couple_who_cannot_share_bedroom", period)
        qualifying_couple = couple & person.benunit.any(member)
        couple_rooms = occupiers_total(claimant_or_partner & qualifying_couple) / 2
        extra = child_rooms + couple_rooms
        # Reg 13D(3), closing words: only if the dwelling has a bedroom
        # additional to those to which the claimant would be entitled if the
        # child or the member of the couple were able to share.
        able_to_share = housing_benefit_bedrooms_if_able_to_share(benunit, period)
        bedrooms = benunit.max(person.household("num_bedrooms", period))
        spare = max_(bedrooms - able_to_share, 0)
        return where(bedrooms > 0, min_(extra, spare), extra)

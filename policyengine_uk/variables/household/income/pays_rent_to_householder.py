from policyengine_uk.model_api import *


class pays_rent_to_householder(Variable):
    value_type = bool
    entity = Person
    label = "liable to pay the householder rent as a boarder or lodger"
    documentation = (
        "Whether this person, outside the household head's benefit unit, is "
        "liable to pay the household head on a commercial basis for their "
        "occupation as a boarder or lodger, so is not the householder's "
        "non-dependant. That covers a person who pays rent for board and "
        "lodging or for lodging (rent_paid_as_boarder or rent_paid_as_lodger "
        "above nil), and the claimant or partner of a benefit unit where a "
        "claimant or partner pays. HB Regs 2006 and HB (SPC) Regs 2006 reg "
        "8(1)(b) treat the partner of a liable person as liable. The Universal "
        "Credit and council tax reduction rules have no such words; the data "
        "hold no agreement, and the model assumes, for every scheme, that a "
        "couple's room binds both members. Nobody else in the payer's benefit "
        "unit is liable: a payer who is not a claimant or partner, such as a "
        "qualifying young person, makes nobody else liable, and a payer's "
        "adult son or daughter who pays nothing stays a non-dependant. The "
        "model takes every such payment to be commercial and the payer not to "
        "be a close relative living there, whom the rules keep as a "
        "non-dependant (HB reg 3(3) with reg 9(1); CTR reg 9(3)). The Family "
        "Resources Survey asks about this rent only for people not related to "
        "the household reference person."
    )
    definition_period = YEAR
    reference = [
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/8",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/8",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/9",
    ]

    def formula(person, period, parameters):
        paid = add(person, period, ["rent_paid_as_boarder", "rent_paid_as_lodger"])
        pays = paid > 0
        claimant_or_partner = person("is_claimant_or_partner", period)
        # HB Regs 2006 reg 8(1)(b): the partner of a liable person is liable.
        partner_pays = person.benunit.any(pays & claimant_or_partner)
        in_head_benunit = person.benunit("benunit_contains_household_head", period)
        return ~in_head_benunit & (pays | (claimant_or_partner & partner_pays))

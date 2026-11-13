from policyengine_uk.model_api import *


class is_looked_after_by_local_authority(Variable):
    value_type = bool
    entity = Person
    label = "looked after by a local authority"
    documentation = (
        "Whether this child or young person is looked after by a local "
        "authority. Only a person under 18 can be (see "
        "is_looked_after_child), so the flag has no effect at 18 or over. A looked-after child who lives in the household, such as "
        "a foster child, is placed with the family whose benefit unit they "
        "are in: no one in it is responsible for them under Universal Credit "
        "(UC Regs 2013 reg 4(6)(a)), they are not a member of the claimant's "
        "household under Housing Benefit and the other legacy schemes (HB "
        "Regs 2006 reg 21(3)), they have no bedroom of their own in the size "
        "criteria, and their carer meets the foster parent condition for an "
        "additional bedroom. Leave it false for a child placed for adoption "
        "(see is_placed_for_adoption) or placed with their own parent, for "
        "whom Universal Credit treats the carer as responsible (reg 4A). "
        "Under Housing Benefit and the other legacy schemes, a child placed "
        "with a parent by a local authority under Children Act 1989 s.22C(2) "
        "is outside the household (HB Regs 2006 reg 21(3)(a)); one flag "
        "cannot represent both, and the model treats such a child as a "
        "household member."
    )
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.legislation.gov.uk/uksi/2015/448/regulation/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4A",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/21",
    )

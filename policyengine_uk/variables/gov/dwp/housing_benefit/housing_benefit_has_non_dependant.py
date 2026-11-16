from policyengine_uk.model_api import *
from policyengine_uk.variables.household.consumption.rent.non_dependant_normally_resides_with import (
    non_dependants_residing_with,
)


class housing_benefit_has_non_dependant(Variable):
    value_type = bool
    entity = BenUnit
    label = "Has a non-dependant residing with them (Housing Benefit)"
    documentation = (
        "Someone in this benefit unit who is a Housing Benefit non-dependant "
        "(is_benefit_unit_non_dependant_for_legacy_benefits: neither a "
        "claimant or partner nor a child or young person, including one "
        "placed with the family as a foster child or for adoption; a "
        "16-year-old outside the Child Benefit young person test is one), "
        "or, for a family liable for the "
        "household's rent (the household head's or a sharer's), anyone in "
        "the household who is a non-dependant (see "
        "is_non_dependant_of_household_head) and normally resides with it. "
        "Where the rent is shared, a non-dependant resides with each joint "
        "occupier that non_dependant_normally_resides_with gives, by default "
        "every one; a joint occupier's own family is never another's "
        "non-dependant, whatever its rent. A boarder's or lodger's family "
        "has none from the householder's household."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/21",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://assets.publishing.service.gov.uk/media/5a758238ed915d6faf2b38a2/lha-guidance-manual.pdf#page=33",
    )

    def formula(benunit, period, parameters):
        # HB Regs 2006 reg 3(1)-(2), (4) and reg 74(5).
        person = benunit.members
        # Reg 3(2)(a) and (c) with regs 19 and 21(3): a member of the benefit
        # unit who is neither the claimant or partner nor a child or young
        # person, whether in the claimant's family or placed with the
        # claimant or partner. The young person test is Child Benefit's (reg
        # 19), with no separate rule for 16-year-olds: one outside it is a
        # non-dependant, and one within it who is not placed makes the
        # claimant a lone parent rather than a single claimant (reg 2(1)), so
        # either way the claimant is not a young individual with no
        # non-dependant (reg 13D(2)(a)(i)).
        within_benefit_unit = benunit.any(
            person("is_benefit_unit_non_dependant_for_legacy_benefits", period)
        )
        liable_family = benunit.any(person("is_liable_for_household_rent", period))
        # Reg 3(1), (2)(d) and (4): a non-dependant of several joint
        # occupiers resides with each of them (LHA Guidance Manual paras
        # 2.050 and 2.110); one who lives with one joint tenant only resides
        # with that tenant alone (para 2.093, example 2). A member of a joint
        # occupier's family is no one's non-dependant, even where the family
        # has no rent of its own.
        non_dependants = non_dependants_residing_with(
            benunit, period, person("is_non_dependant_of_household_head", period)
        )
        return within_benefit_unit | (liable_family & (non_dependants > 0))

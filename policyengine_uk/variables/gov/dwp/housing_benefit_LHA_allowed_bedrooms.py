from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_allowed_bedrooms import (
    child_bedrooms,
)
from policyengine_uk.variables.household.consumption.rent.non_dependant_normally_resides_with import (
    non_dependants_residing_with,
)


def housing_benefit_other_occupiers(benunit, period, other_occupier):
    """For each family, the sum of ``other_occupier`` (a count or weight for
    each occupier outside every family liable for the household's rent, zero
    for anyone else) over the people who occupy its dwelling (HB Regs 2006
    reg 13D(12)), before the caller limits it to claims by families liable
    for the rent. A boarder or lodger who pays the householder occupies the
    dwelling of every such claim. A non-dependant, and anyone else who pays
    nothing, counts for each joint occupier they normally reside with (LHA
    Guidance Manual paras 2.093 and 2.110; see
    non_dependant_normally_resides_with), by default every one."""
    person = benunit.members
    boarder_or_lodger = person("pays_rent_to_householder", period)
    of_every_claim = benunit.max(
        person.household.sum(other_occupier * boarder_or_lodger)
    )
    non_dependants = non_dependants_residing_with(
        benunit, period, other_occupier * ~boarder_or_lodger
    )
    return of_every_claim + non_dependants


class housing_benefit_LHA_allowed_bedrooms(Variable):
    value_type = float
    entity = BenUnit
    label = "Bedrooms in the Housing Benefit size criteria"
    documentation = (
        "Housing Benefit size criteria over the claim's occupiers: one "
        "bedroom for each couple, one for each other occupier aged 16 or "
        "over, the children's bedrooms, pairing children across all the "
        "occupiers, and the additional bedrooms for overnight care and "
        "qualifying parents or carers (see "
        "housing_benefit_LHA_additional_bedrooms). Occupiers are everyone "
        "who lives in the dwelling as their home except a joint tenant "
        "outside the claimant's household. For the household head's family "
        "or a sharer's, that is its own family, the household's "
        "non-dependants and anyone paying the householder rent, with their "
        "children (but not the other families liable for the rent). Where "
        "the rent is shared, a non-dependant and their children count for "
        "each joint occupier they normally reside with, by default every one "
        "(see non_dependant_normally_resides_with). A "
        "boarder's or lodger's own claim counts only their own family. A "
        "child or young person placed with the claimant or partner as a "
        "foster child or for adoption does not occupy the claimant's "
        "dwelling, so the claimant's own claim leaves them out; a child "
        "placed with a non-dependant, boarder or lodger occupies the "
        "claimant's dwelling and counts in the claimant's size criteria. "
        "Couples and children who cannot share a bedroom are not modelled."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/21",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/21",
    )

    def formula(benunit, period, parameters):
        # HB Regs 2006 reg 13D(3) with "occupiers" as defined in 13D(12).
        person = benunit.members
        age = person("age", period)
        claimant_or_partner = person("is_claimant_or_partner", period)
        liable_family = person.benunit.any(
            person("is_liable_for_household_rent", period)
        )
        # Members of families not liable for the household's rent:
        # non-dependants and people paying the householder.
        other = ~liable_family
        is_liable_claim = benunit.any(person("is_liable_for_household_rent", period))
        # HB Regs 2006 reg 21(3): a child or young person placed with the
        # claimant or partner as a foster child or for adoption does not
        # occupy the claimant's dwelling. Every limb names a placement "with
        # the claimant or his partner", so a child placed with a
        # non-dependant, boarder or lodger is one of the persons who occupy
        # the claimant's dwelling as their home (13D(12)) and counts in the
        # claimant's size criteria, while the carer's own claim leaves them
        # out.
        placed = person("is_child_or_young_person_placed_with_family", period)

        # A non-dependant shared by joint tenants counts in each one's size
        # criteria (LHA Guidance Manual para 2.110); one who lives with one
        # joint tenant only counts for that tenant alone (para 2.093, example
        # 2). See housing_benefit_other_occupiers.
        def occupiers_total(values):
            own = benunit.sum(values & ~placed)
            others = housing_benefit_other_occupiers(benunit, period, values & other)
            return own + where(is_liable_claim, others, 0)

        # 13D(3)(zb), (a): one bedroom for each couple or single claimant. A
        # family counts as a couple only where both members are present and
        # it is a couple (is_couple), so the halves always pair.
        couple = (person.benunit.sum(claimant_or_partner) == 2) & person.benunit(
            "is_couple", period
        )
        adult_units = (
            occupiers_total(claimant_or_partner)
            - occupiers_total(claimant_or_partner & couple) / 2
        )
        # 13D(3)(b): any other person who is not a child.
        other_adults = occupiers_total((age >= 16) & ~claimant_or_partner)
        # 13D(3)(c)-(e): the occupiers' children, the claimant's own and
        # other families', share rooms with each other.
        under_16 = age < 16
        male = person("is_male", period)
        under_10 = age < 10
        rooms_for_children = child_bedrooms(
            occupiers_total(under_10 & male),
            occupiers_total(~under_10 & under_16 & male),
            occupiers_total(under_10 & ~male),
            occupiers_total(~under_10 & under_16 & ~male),
        )
        # 13D(3A) and (3B): additional bedrooms.
        additional = benunit("housing_benefit_LHA_additional_bedrooms", period)
        return max_(adult_units, 1) + other_adults + rooms_for_children + additional

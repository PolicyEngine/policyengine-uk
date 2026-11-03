from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.LHA_allowed_bedrooms import (
    child_bedrooms,
)


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
        "children (but not the other families liable for the rent). A "
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

        def occupiers_total(values):
            own = benunit.sum(values & ~placed)
            others = benunit.max(person.household.sum(values & other))
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

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
        "over, and the children's bedrooms, pairing children across all the "
        "occupiers. Occupiers are everyone who lives in the dwelling as their "
        "home except a joint tenant outside the claimant's household. For "
        "the household head's family or a sharer's, that is its own family, "
        "the household's non-dependants and anyone paying the householder "
        "rent (but not the other families liable for the rent). A boarder's "
        "or lodger's own claim counts only their own family. Couples who "
        "cannot share a bedroom and the additional bedrooms for overnight "
        "care or foster parents are not modelled."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/13D",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/13D",
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

        def occupiers_total(values):
            own = benunit.sum(values)
            others = benunit.max(person.household.sum(values * other))
            return own + where(is_liable_claim, others, 0)

        # 13D(3)(zb), (a): one bedroom for each couple or single claimant.
        adult_units = (
            occupiers_total(
                claimant_or_partner & (person.benunit.sum(claimant_or_partner) > 0)
            )
            - occupiers_total(
                claimant_or_partner & (person.benunit.sum(claimant_or_partner) == 2)
            )
            / 2
        )
        # 13D(3)(b): any other person who is not a child.
        other_adults = occupiers_total((age >= 16) & ~claimant_or_partner)
        under_16 = age < 16
        male = person("is_male", period)
        under_10 = age < 10
        rooms_for_children = child_bedrooms(
            occupiers_total(under_10 & male),
            occupiers_total(~under_10 & under_16 & male),
            occupiers_total(under_10 & ~male),
            occupiers_total(~under_10 & under_16 & ~male),
        )
        return max_(adult_units, 1) + other_adults + rooms_for_children

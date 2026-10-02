from policyengine_uk.model_api import *


class uc_non_dependants_counted(Variable):
    value_type = bool
    entity = BenUnit
    label = "Universal Credit claim that counts the household's non-dependants"
    documentation = (
        "Whether this family's Universal Credit claim counts the household's "
        "non-dependants. A non-dependant normally lives with every renter "
        "liable for the household's rent, but is not one for a renter if "
        "already treated as a non-dependant in another Universal Credit claim "
        "by someone liable for the same accommodation. The model gives them "
        "to the first such claim: the household head's family if it is "
        "eligible for and claims Universal Credit, otherwise the first family "
        "liable for a share of the rent that does (in the order the families "
        "are given). A boarder or lodger has "
        "none: the householder's household is excluded from their extended "
        "benefit unit."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9"

    def formula(benunit, period, parameters):
        # UC Regs 2013 Sch 4 para 9(2)(e)-(f).
        person = benunit.members
        liable_family = benunit.any(person("is_liable_for_household_rent", period))
        claims = (
            liable_family
            & benunit("is_uc_eligible", period)
            & benunit("would_claim_uc", period)
        )
        head_family = benunit.any(person("is_household_head", period))
        # Order the claims: the household head's family first, then the
        # others in the order the families were given.
        position = np.arange(len(head_family))
        order = where(head_family, -1, position)
        key = where(claims, order, np.inf)
        first = benunit.max(person.household.min(benunit.project(key)))
        return claims & (key == first)

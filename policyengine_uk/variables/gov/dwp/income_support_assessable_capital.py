from policyengine_uk.model_api import *


class income_support_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Assessable capital for Income Support"
    documentation = (
        "Household capital apportioned to the benefit unit for the Income Support "
        "capital test. Because the dataset only stores these stocks at household "
        "level, the model allocates full household capital to any benunit on the "
        "IS claim path and only falls back to an adult-share proxy when nobody in "
        "the household is on that path. "
        "Person-level sources, such as a Lifetime ISA, count only for the "
        "holder's own benunit, and only when the holder is its claimant or "
        "partner (is_uc_claimant): a dependant's capital is not the claimant's."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        sources = IS.means_test.capital.sources
        person = benunit.members
        would_claim_is = benunit("would_claim_IS", period)

        # The data model stores these capital stocks at household level. For the
        # live Income Support path, avoid diluting capital across separate claims:
        # any benunit on the IS claim path gets the full observed household total.
        # If nobody in the household is on that path, fall back to an all-adults
        # proxy so direct inspection still returns a usable value.
        household_capital = sum(
            benunit.max(person.household(source, period)) for source in sources
        )
        benunit_adults = add(benunit, period, ["is_adult"])
        household_claiming_adults = benunit.max(
            person.household.sum(
                person("is_adult", period) & person.benunit("would_claim_IS", period)
            )
        )
        household_adults = benunit.max(
            person.household.sum(person.household.members("is_adult", period))
        )
        fallback_divisor = max_(1, household_adults)
        claiming_proxy = where(would_claim_is, household_capital, 0)
        fallback_proxy = household_capital * benunit_adults / fallback_divisor
        claimant_or_partner = person("is_uc_claimant", period)
        person_capital = sum(
            benunit.sum(person(source, period) * claimant_or_partner)
            for source in IS.means_test.capital.person_sources
        )
        household_share = where(
            household_claiming_adults > 0, claiming_proxy, fallback_proxy
        )
        return household_share + person_capital

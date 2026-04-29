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
        "the household is on that path."
    )
    definition_period = YEAR
    unit = GBP

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
        return where(household_claiming_adults > 0, claiming_proxy, fallback_proxy)

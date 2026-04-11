from policyengine_uk.model_api import *


class income_support_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Assessable capital for Income Support"
    documentation = (
        "Household capital apportioned to the benefit unit for the Income Support "
        "capital test."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        sources = IS.means_test.capital.sources
        person = benunit.members

        # The data model stores these capital stocks at household level, so split
        # them across the benefit units in the household using an adult-share
        # proxy rather than treating all benunits as equal-sized claim units.
        household_capital = sum(
            benunit.max(person.household(source, period)) for source in sources
        )
        benunit_adults = add(benunit, period, ["is_adult"])
        household_adults = benunit.max(
            person.household.sum(person.household.members("is_adult", period))
        )
        adult_divisor = max_(1, household_adults)
        return household_capital * benunit_adults / adult_divisor

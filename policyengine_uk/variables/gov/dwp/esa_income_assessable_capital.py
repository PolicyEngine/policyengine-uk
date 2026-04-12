from policyengine_uk.model_api import *


class esa_income_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Assessable capital for income-related ESA"
    documentation = (
        "Household capital apportioned to the benefit unit for the income-related "
        "ESA capital test. Because the dataset only stores these stocks at "
        "household level, the model allocates full household capital to any "
        "benunit with a reported income-related ESA award and only falls back to "
        "an adult-share proxy when nobody in the household is on that reported "
        "claim path."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        ESA = parameters(period).gov.dwp.ESA.income
        sources = ESA.capital.sources
        person = benunit.members
        claiming_esa_income = add(benunit, period, ["esa_income_reported"]) > 0

        household_capital = sum(
            benunit.max(person.household(source, period)) for source in sources
        )
        benunit_adults = add(benunit, period, ["is_adult"])
        household_reporting_claimants = benunit.max(
            person.household.sum(
                person("is_adult", period) & (person("esa_income_reported", period) > 0)
            )
        )
        household_adults = benunit.max(
            person.household.sum(person.household.members("is_adult", period))
        )
        fallback_divisor = max_(1, household_adults)
        claiming_proxy = where(claiming_esa_income, household_capital, 0)
        fallback_proxy = household_capital * benunit_adults / fallback_divisor
        return where(household_reporting_claimants > 0, claiming_proxy, fallback_proxy)

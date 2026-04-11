from policyengine_uk.model_api import *


class housing_benefit_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Housing Benefit assessable capital"
    documentation = (
        "Housing Benefit capital counted from the configured capital sources, "
        "allocated across benunits using a household adult-share proxy."
    )
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        household = benunit.household
        person = benunit.members
        any_over_SP_age = benunit.any(person("is_SP_age", period))
        p = parameters(period).gov.dwp.housing_benefit.means_test.capital
        household_capital = add(household, period, p.sources)
        benunit_adults = add(benunit, period, ["is_adult"])
        household_adults = benunit.max(
            person.household.sum(person.household.members("is_adult", period))
        )
        adult_divisor = max_(1, household_adults)
        household_capital_proxy = where(
            household_adults > 0,
            household_capital * benunit_adults / adult_divisor,
            0,
        )
        guarantee_credit = any_over_SP_age & (benunit("guarantee_credit", period) > 0)
        return where(guarantee_credit, 0, max_(0, household_capital_proxy))

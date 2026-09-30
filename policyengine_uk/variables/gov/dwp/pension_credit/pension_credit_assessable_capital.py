from policyengine_uk.model_api import *


class pension_credit_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Pension Credit assessable capital"
    documentation = (
        "Pension Credit capital counted from the configured capital sources, "
        "split only across pension-age adults in the household so pensioner "
        "couples pool capital together without dilution by unrelated working-"
        "age adults."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK

    def formula(benunit, period, parameters):
        household = benunit.household
        person = benunit.members
        p = parameters(period).gov.dwp.pension_credit.income.capital
        household_capital = sum(household(source, period) for source in p.sources)
        # Pension-age adults: those who have attained the qualifying age for
        # State Pension Credit (State Pension Credit Act 2002 s.1(6)).
        pension_age = person("has_attained_state_pension_credit_qualifying_age", period)
        any_pension_age = benunit.any(pension_age)
        benunit_pension_age_adults = benunit.sum(pension_age)
        household_pension_age_adults = benunit.max(
            person.household.sum(
                person.household.members(
                    "has_attained_state_pension_credit_qualifying_age", period
                )
            )
        )
        adult_divisor = max_(1, household_pension_age_adults)
        household_capital_proxy = (
            household_capital * benunit_pension_age_adults / adult_divisor
        )
        return where(any_pension_age, max_(0, household_capital_proxy), 0)

from policyengine_uk.model_api import *


class uc_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit assessable capital"
    documentation = (
        "Universal Credit capital counted from the configured capital sources, "
        "with benunit-reported overrides when available. Household sources are "
        "allocated by the household proxy; person-level sources, such as a "
        "Lifetime ISA, count only in the holder's own benunit."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK

    def formula(benunit, period, parameters):
        household = benunit.household
        p = parameters(period).gov.dwp.universal_credit.means_test
        household_capital = sum(
            household(source, period) for source in p.capital.sources
        )
        person_capital = sum(
            benunit.sum(benunit.members(source, period))
            for source in p.capital.person_sources
        )
        benunit_adults = add(benunit, period, ["is_adult"])
        household_reported_capital = household("household_uc_reported_capital", period)
        household_unreported_adults = household(
            "household_uc_unreported_adults", period
        )
        adult_divisor = max_(1, household_unreported_adults)
        reported_capital = benunit("uc_reported_capital", period)
        use_reported_capital = reported_capital >= 0
        residual_household_capital = max_(
            0, household_capital - household_reported_capital
        )
        household_capital_proxy = where(
            household_unreported_adults > 0,
            residual_household_capital * benunit_adults / adult_divisor,
            0,
        )
        assessed_capital = where(
            use_reported_capital,
            reported_capital,
            household_capital_proxy + person_capital,
        )
        return max_(0, assessed_capital)

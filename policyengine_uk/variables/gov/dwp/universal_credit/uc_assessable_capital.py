from policyengine_uk.model_api import *


class uc_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit assessable capital"
    documentation = (
        "Universal Credit capital counted from the configured capital sources, "
        "with benunit-reported overrides when available, and with a holding "
        "in a company the person stands as sole owner or partner of replaced "
        "by the company's capital."
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
        benunit_adults = add(benunit, period, ["is_adult"])
        household_reported_capital = household("household_uc_reported_capital", period)
        household_unreported_adults = household(
            "household_uc_unreported_adults", period
        )
        adult_divisor = max_(1, household_unreported_adults)
        reported_capital = benunit("uc_reported_capital", period)
        use_reported_capital = reported_capital >= 0
        # A person who stands as sole owner or partner of a company has their
        # holding in it disregarded and is treated as possessing the company's
        # capital (or their share of it) instead (UC Regs 2013 reg. 77(2),
        # (3)(a)). Holdings of people in unreported benunits leave the
        # household pool before it is shared out; a reporting benunit's
        # holdings come off its own reported capital. Neither subtraction can
        # take capital below zero.
        unreported_holdings = household(
            "household_uc_unreported_company_holdings", period
        )
        residual_household_capital = max_(
            0, household_capital - household_reported_capital - unreported_holdings
        )
        household_capital_proxy = where(
            household_unreported_adults > 0,
            residual_household_capital * benunit_adults / adult_divisor,
            0,
        )
        own_holdings = add(benunit, period, ["uc_company_holding_disregard"])
        assessed_capital = where(
            use_reported_capital,
            max_(0, reported_capital - own_holdings),
            household_capital_proxy,
        )
        company_capital = add(benunit, period, ["uc_company_capital"])
        return max_(0, assessed_capital) + company_capital

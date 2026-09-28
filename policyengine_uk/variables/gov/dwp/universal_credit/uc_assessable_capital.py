from policyengine_uk.model_api import *


class uc_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit assessable capital"
    documentation = (
        "Universal Credit capital counted from the configured capital sources, "
        "with benunit-reported overrides when available. PolicyEngine allocates "
        "the remaining household capital between unreported benefit units in "
        "proportion to their claimant and partner counts, including units that "
        "do not receive Universal Credit. This allocation is a modelling "
        "convention when capital ownership is unobserved, not a statutory rule. "
        "The claimant and partner owner set follows section 5 of the Welfare "
        "Reform Act 2012 and regulation 18 of the Universal Credit Regulations."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/5",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/18",
    )

    def formula(benunit, period, parameters):
        household = benunit.household
        p = parameters(period).gov.dwp.universal_credit.means_test
        household_capital = sum(
            household(source, period) for source in p.capital.sources
        )
        benunit_claimants = add(benunit, period, ["is_uc_claimant"])
        household_reported_capital = household("household_uc_reported_capital", period)
        household_unreported_claimants = household(
            "household_uc_unreported_claimants", period
        )
        claimant_divisor = max_(1, household_unreported_claimants)
        reported_capital = benunit("uc_reported_capital", period)
        use_reported_capital = reported_capital >= 0
        residual_household_capital = max_(
            0, household_capital - household_reported_capital
        )
        household_capital_proxy = where(
            household_unreported_claimants > 0,
            residual_household_capital * benunit_claimants / claimant_divisor,
            0,
        )
        assessed_capital = where(
            use_reported_capital,
            reported_capital,
            household_capital_proxy,
        )
        return max_(0, assessed_capital)

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
        "Reform Act 2012 and regulation 18 of the Universal Credit Regulations. "
        "Person-level sources, such as a Lifetime ISA, count only for the "
        "holder's own benunit, and only when the holder is its claimant or "
        "partner (is_uc_claimant): a dependant's capital is not the claimant's. "
        "A claimant or partner who stands as sole owner or partner of a "
        "company has their holding in it disregarded and the company's capital "
        "counted instead (regulation 77(2))."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/5",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/18",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
    )

    def formula(benunit, period, parameters):
        household = benunit.household
        p = parameters(period).gov.dwp.universal_credit.means_test
        household_capital = sum(
            household(source, period) for source in p.capital.sources
        )
        benunit_claimants = add(benunit, period, ["is_uc_claimant"])
        claimant_or_partner = benunit.members("is_uc_claimant", period)
        person_capital = sum(
            benunit.sum(benunit.members(source, period) * claimant_or_partner)
            for source in p.capital.person_sources
        )
        household_reported_capital = household("household_uc_reported_capital", period)
        household_unreported_claimants = household(
            "household_uc_unreported_claimants", period
        )
        claimant_divisor = max_(1, household_unreported_claimants)
        reported_capital = benunit("uc_reported_capital", period)
        use_reported_capital = reported_capital >= 0
        # A person who stands as sole owner or partner of a company has their
        # holding in it disregarded and is treated as possessing the company's
        # capital (or their share of it) instead (UC Regs 2013 reg. 77(2),
        # (3)(a)). Holdings of people in unreported benunits leave the
        # household pool before it is shared out; a reporting benunit's
        # claimant and partner's holdings come off its reported capital.
        # Neither subtraction can take capital below zero. Only the claimant
        # and partner's company capital is theirs to count.
        unreported_holdings = household(
            "household_uc_unreported_company_holdings", period
        )
        residual_household_capital = max_(
            0, household_capital - household_reported_capital - unreported_holdings
        )
        household_capital_proxy = where(
            household_unreported_claimants > 0,
            residual_household_capital * benunit_claimants / claimant_divisor,
            0,
        )
        own_holdings = benunit.sum(
            benunit.members("uc_company_holding_disregard", period)
            * claimant_or_partner
        )
        assessed_capital = where(
            use_reported_capital,
            max_(0, reported_capital - own_holdings),
            household_capital_proxy + person_capital,
        )
        company_capital = benunit.sum(
            benunit.members("uc_company_capital", period) * claimant_or_partner
        )
        return max_(0, assessed_capital) + company_capital

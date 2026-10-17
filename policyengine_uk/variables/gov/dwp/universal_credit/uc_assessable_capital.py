from policyengine_uk.model_api import *


class uc_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit assessable capital"
    documentation = (
        "Countable capital of the claimant and partner. An explicit nonnegative "
        "uc_reported_capital, including zero, replaces ordinary capital sources "
        "before the existing regulation 77 company substitution. Otherwise "
        "a nonnegative benunit_reported_capital replaces financial household "
        "and person-level proxies only; it does not replace countable property. "
        "Observed financial totals reduce the household financial pool before "
        "its residual is allocated by claimant/partner counts to units with "
        "neither report. Under this inherited financial convention, another "
        "unit's financial report can change a missing-report unit's capital. "
        "A complete override is never subtracted from that "
        "financial pool because its asset decomposition is unknown. Property "
        "is valued separately in the assessment year and allocated across ALL "
        "claimant/partner adults, including non-UC units and complete-override "
        "units, whose shares are consumed rather than redistributed. Property "
        "allocation depends only on claimant/partner adult counts and is "
        "independent of other units' financial reports. These "
        "allocations are assumptions about unobserved ownership, not law. "
        "Person-level proxies count only claimants/partners, not dependants. "
        "Under regulation 77, disregarded company holdings are replaced by "
        "the claimant/partner's share of company capital."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/5",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/18",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/49",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/77",
    )

    def formula(benunit, period, parameters):
        household = benunit.household
        p = parameters(period).gov.dwp.universal_credit.means_test.capital
        household_financial_capital = sum(
            household(source, period) for source in p.sources
        )
        claimant_or_partner = benunit.members("is_uc_claimant", period)
        benunit_claimants = benunit.sum(claimant_or_partner)
        person_capital = sum(
            benunit.sum(benunit.members(source, period) * claimant_or_partner)
            for source in p.person_sources
        )
        financial_report = benunit("benunit_reported_capital", period)
        complete_override = benunit("uc_reported_capital", period)
        unreported_claimants = household("household_uc_unreported_claimants", period)
        # Complete overrides may include property, so only observed FINANCIAL
        # totals can be subtracted from this financial-only pool.
        residual_financial_capital = max_(
            0,
            household_financial_capital
            - household("household_uc_reported_financial_capital", period)
            - household("household_uc_pool_company_holdings", period),
        )
        financial_proxy = where(
            unreported_claimants > 0,
            residual_financial_capital
            * benunit_claimants
            / max_(1, unreported_claimants),
            0,
        )
        own_holdings = benunit.sum(
            benunit.members("uc_company_holding_disregard", period)
            * claimant_or_partner
        )
        financial_capital = where(
            financial_report >= 0,
            max_(0, financial_report - own_holdings),
            financial_proxy + person_capital,
        )
        assessed_capital = where(
            complete_override >= 0,
            max_(0, complete_override - own_holdings),
            financial_capital + benunit("uc_property_capital", period),
        )
        company_capital = benunit.sum(
            benunit.members("uc_company_capital", period) * claimant_or_partner
        )
        return max_(0, assessed_capital) + company_capital

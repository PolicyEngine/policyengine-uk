from policyengine_uk.model_api import *
from policyengine_uk.utils.capital_valuation import (
    counted_share,
    exact_amount,
    round_to_penny,
    valued_capital,
)
from policyengine_uk.variables.gov.dwp.universal_credit.household_uc_company_holding_pool_scale import (
    HOLDINGS_SOURCE,
)


class uc_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit assessable capital"
    documentation = (
        "Countable capital of the claimant and partner. An explicit nonnegative "
        "uc_reported_capital, including zero, replaces ordinary capital sources "
        "before the existing regulation 77 company substitution. Otherwise "
        "a nonnegative benunit_reported_capital replaces financial household "
        "and person-level proxies; it does not replace separately valued "
        "domestic, overseas or unclassified other property. "
        "Complete overrides, otherwise observed financial totals, reduce the "
        "household financial pool before "
        "its residual is allocated by claimant/partner counts to units with "
        "neither report. Under this inherited financial convention, another "
        "unit's financial report or complete override can change a "
        "missing-report unit's capital. Subtracting a complete override is "
        "a pool-allocation convention, not an observed asset breakdown. Property "
        "is valued separately in the assessment year and allocated across ALL "
        "claimant/partner adults, including non-UC units and complete-override "
        "units, whose shares are consumed rather than redistributed. Property "
        "allocation depends only on claimant/partner adult counts and is "
        "independent of other units' financial reports. These "
        "allocations are assumptions about unobserved ownership, not law. "
        "Person-level proxies count only claimants/partners, not dependants. "
        "Under regulation 77, disregarded company holdings are replaced by "
        "the claimant/partner's share of company capital. Regulation 49(1) "
        "values the financial pool's sources whose sale would incur expenses "
        "(sale_expenses.sources, shares in share_like_capital) at 90%, and a "
        "disregarded holding comes off at the value at which it was counted: "
        "90% in the pool and in a complete override, which is a countable "
        "figure, and in full from a recorded financial total, which is used "
        "without valuation. Every amount calculated is rounded to the nearest "
        "penny (regulation 6(1)), including this capital, which is tested "
        "against the limit."
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
        household_financial_capital = valued_capital(
            lambda variable: household(variable, period), p
        )
        # A reg. 77 holding sits in share_like_capital, so it is counted at the
        # same 90% as the shares around it wherever they are valued.
        holding_value = counted_share(p.sale_expenses, HOLDINGS_SOURCE)
        claimant_or_partner = benunit.members("is_uc_claimant", period)
        benunit_claimants = benunit.sum(claimant_or_partner)
        person_capital = sum(
            benunit.sum(
                exact_amount(benunit.members(source, period)) * claimant_or_partner
            )
            for source in p.person_sources
        )
        financial_report = exact_amount(benunit("benunit_reported_capital", period))
        complete_override = exact_amount(benunit("uc_reported_capital", period))
        unreported_claimants = household("household_uc_unreported_claimants", period)
        # Each unit consumes its complete override, otherwise its financial
        # report, from the financial pool under the inherited convention.
        residual_financial_capital = max_(
            0,
            household_financial_capital
            - exact_amount(household("household_uc_reported_financial_capital", period))
            - exact_amount(household("household_uc_pool_company_holdings", period)),
        )
        financial_proxy = where(
            unreported_claimants > 0,
            residual_financial_capital
            * benunit_claimants
            / max_(1, unreported_claimants),
            0,
        )
        own_holdings = benunit.sum(
            exact_amount(benunit.members("uc_company_holding_disregard", period))
            * claimant_or_partner
        )
        financial_capital = where(
            financial_report >= 0,
            max_(0, financial_report - own_holdings),
            financial_proxy + person_capital,
        )
        assessed_capital = where(
            complete_override >= 0,
            max_(
                0,
                complete_override
                - round_to_penny(own_holdings * holding_value, p.round_down),
            ),
            financial_capital + exact_amount(benunit("uc_property_capital", period)),
        )
        company_capital = benunit.sum(
            exact_amount(benunit.members("uc_company_capital", period))
            * claimant_or_partner
        )
        # Every amount is rounded to the nearest penny (reg. 6(1)), the
        # capital tested against the limit included.
        return round_to_penny(max_(0, assessed_capital) + company_capital, p.round_down)

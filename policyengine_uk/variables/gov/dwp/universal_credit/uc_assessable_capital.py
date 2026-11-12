from policyengine_uk.model_api import *
from policyengine_uk.utils.capital_valuation import (
    counted_share,
    exact_amount,
    round_to_penny,
    valued_capital,
    valued_person_capital,
)
from policyengine_uk.variables.gov.dwp.universal_credit.household_uc_company_holding_pool_scale import (
    HOLDINGS_SOURCE,
)
from policyengine_uk.variables.gov.dwp._person_capital_pool import (
    pooled_person_capital,
)


class uc_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit assessable capital"
    documentation = (
        "Countable capital of the claimant and partner. An explicit nonnegative "
        "uc_reported_capital, including zero, replaces ordinary capital sources before "
        "the regulation 77 company substitution. Otherwise a nonnegative "
        "benunit_reported_capital replaces financial household and person-level "
        "proxies only; it does not replace countable property. The formula subtracts "
        "complete overrides, otherwise observed financial totals, from the household "
        "financial pool, and allocates the financial remainder by claimant and partner "
        "counts among units without either report. Under this inherited convention, "
        "another unit's financial report or complete override can change a "
        "missing-report unit's capital. The formula values property separately in the "
        "assessment year and allocates it across all claimant and partner adults, "
        "including non-UC units and complete-override units, whose shares it doesn't "
        "redistribute; other units' financial reports leave that allocation unchanged. "
        "These allocations assume ownership the data don't record, and no regulation "
        "sets them. Person-level proxies count only claimants and partners, not "
        "dependants. The formula subtracts each bounded cash and stocks and shares ISA "
        "balance from its household source and counts it in the holder's unit, except "
        "for the claimant and partner of a unit that reports its capital: it leaves "
        "their ISAs in the pool and subtracts the report, as for their company "
        "holdings. Under regulation 77, it replaces disregarded company holdings with "
        "the claimant's or partner's share of company capital. Regulation 49(1) "
        "values the financial pool's sources whose sale would incur expenses "
        "(sale_expenses.sources: directly held shares, and all of an "
        "unitemised corporate_wealth) at 90%. The formula counts a stocks and "
        "shares ISA balance it moves out of share_like_capital_without_sale_expenses "
        "at its withdrawal value (ADM H1656-H1658). A disregarded holding comes off at the value at which the formula "
        "counted it: 90% in the pool and in a complete override, which is a "
        "countable figure, and in full from a recorded financial total, which the "
        "formula uses without valuation. The formula rounds every amount it "
        "calculates to the nearest penny (regulation 6(1)), including this "
        "capital, which it tests against the limit."
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
        person = benunit.members
        claimant_or_partner = person("is_uc_claimant", period)
        # For a unit with a report or complete override, leave its claimant's
        # and partner's ISAs in the pool and subtract the report, as for their
        # company holdings. Subtract every other person's ISA here.
        covered = claimant_or_partner & (
            (person.benunit("benunit_reported_capital", period) >= 0)
            | (person.benunit("uc_reported_capital", period) >= 0)
        )
        household_financial_capital = valued_capital(
            lambda source: (
                household(source, period)
                - pooled_person_capital(benunit, source, period, p, ~covered)
            ),
            p,
        )
        # A reg. 77 holding sits in the shares with sale expenses, so it is
        # counted at the same 90% as the shares around it wherever they are
        # valued.
        holding_value = counted_share(p.sale_expenses, HOLDINGS_SOURCE)
        benunit_claimants = benunit.sum(claimant_or_partner)
        person_capital = valued_person_capital(
            benunit, period, parameters, p, claimant_or_partner
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

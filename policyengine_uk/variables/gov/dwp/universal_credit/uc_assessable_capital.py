from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp._person_capital_pool import (
    counted_person_sources,
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
        "the claimant's or partner's share of company capital."
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
        household_financial_capital = sum(
            household(source, period)
            - pooled_person_capital(benunit, source, period, p, ~covered)
            for source in p.sources
        )
        benunit_claimants = benunit.sum(claimant_or_partner)
        person_capital = sum(
            benunit.sum(person(source, period) * claimant_or_partner)
            for source in counted_person_sources(p)
        )
        financial_report = benunit("benunit_reported_capital", period)
        complete_override = benunit("uc_reported_capital", period)
        unreported_claimants = household("household_uc_unreported_claimants", period)
        # Each unit consumes its complete override, otherwise its financial
        # report, from the financial pool under the inherited convention.
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
